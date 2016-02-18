from datetime import datetime
import os

from segue.core import db, logger, config
from segue.errors import NotAuthorized
from segue.product.errors import NoSuchProduct, ProductExpired
from segue.validation import CPFValidator, CNPJValidator, ZipCodeValidator

from factories import BuyerFactory, PurchaseFactory
from filters import PurchaseFilterStrategies, PaymentFilterStrategies

from segue.mailer import MailerService

from pagseguro import PagSeguroPaymentService
from boleto    import BoletoPaymentService
from cash      import CashPaymentService
from models    import Purchase, Payment
from errors    import NoSuchPayment, NoSuchPurchase, PurchaseAlreadySatisfied, PurchaseIsStale
from errors    import InvalidDocumentNumber, InvalidZipCodeNumber

from segue.purchase.promocode import PromoCodeService, PromoCodePaymentService
from segue.purchase.factories import DonationClaimCheckFactory
from segue.document.services import DocumentService

import schema

class OnlinePaymentDeadline(object):
    def __init__(self, override_config=None):
        self.config = override_config or config

    def is_past(self):
        return datetime.now() > self.config.ONLINE_PAYMENT_DEADLINE

    def enforce(self):
        if self.is_past():
            raise DeadlineReached()

class PurchaseService(object):
    def __init__(self, db_impl=None, payments=None, filters=None, deadline=None, promocode=None):
        self.db = db_impl or db
        self.payments = payments or PaymentService()
        self.filters = filters or PurchaseFilterStrategies()
        self.deadline = deadline or OnlinePaymentDeadline()
        self.promocode_service = promocode or PromoCodeService()

    def by_range(self, start, end):
        return Purchase.query.filter(Purchase.id.between(start, end)).order_by(Purchase.id)

    def get_by_hash(self, hash_code, strict=True):
        purchase = Purchase.query.filter(Purchase.hash_code == hash_code).first()
        if purchase: return purchase
        if strict: raise NoSuchPurchase()
        return None

    def migrate_type(self, purchase_id, new_type):
        purchase = self.get_one(purchase_id, strict=True, check_ownership=False)
        purchase.kind = new_type
        db.session.add(purchase)
        db.session.commit()
        db.session.expunge(purchase)
        db.session.close()

        return self.get_one(purchase_id, strict=True, check_ownership=False)

    def current_mode(self):
        return 'reservation' if self.deadline.is_past() else 'online'

    def query(self, by=None, **kw):
        filter_list = self.filters.given(**kw)
        return Purchase.query.filter(*filter_list).all()

    def create(self, buyer_data, product, account, commit=True, **extra):
        buyer    = BuyerFactory.from_json(buyer_data, schema.buyer)
        self._validate_buyer(buyer)
        purchase = PurchaseFactory.create(buyer, product, account, **extra)
        logger.info(buyer_data)

        self.db.session.add(buyer)
        self.db.session.add(purchase)

        if 'hash_code' in buyer_data:
            self.payments.create(purchase, 'promocode', { 'hash_code': buyer_data['hash_code'] })

        if commit:
            self.db.session.commit()
        return purchase

    def get_one(self, purchase_id, by=None, strict=False, check_ownership=True):
        purchase = Purchase.query.get(purchase_id)
        if strict and not purchase: raise NoSuchPurchase()
        if not purchase: return None
        if not check_ownership: return purchase
        if not self.check_ownership(purchase, by): raise NotAuthorized()

        return purchase

    def check_ownership(self, purchase, alleged):
        return purchase.customer and purchase.customer.can_be_acessed_by(alleged)

    def create_payment(self, purchase_id, payment_method, payment_data, by=None):
        purchase = self.get_one(purchase_id, by=by)
        if purchase.can_start_payment:
            instructions, payment = self.payments.create(purchase, payment_method, payment_data)
            return instructions
        raise ProductExpired()

    def clone_purchase(self, purchase_id, by=None, commit=True):
        purchase = self.get_one(purchase_id, by=by)
        if not purchase: return None

        if purchase.satisfied:
            raise PurchaseAlreadySatisfied()

        replacement_product = purchase.product.similar_products().first()
        if not replacement_product:
            raise NoSuchProduct()

        cloned_purchase = purchase.clone()
        cloned_purchase.customer = purchase.customer
        cloned_purchase.product = replacement_product
        db.session.add(cloned_purchase)
        if commit: db.session.commit()
        return cloned_purchase

    def check_promocode(self, hash, by=None):
        logger.info("received promocode hash: " + hash)
        return self.promocode_service.check(hash)

    def give_speaker_ticket(self, account, commit=True):
        from segue.proposal.models import SpeakerProduct
        product = SpeakerProduct.query.first()
        purchase = PurchaseFactory.get_or_create(None, product, account)
        purchase.status = 'paid'
        db.session.add(purchase)
        if commit: db.session.commit()
        return purchase

    def give_fresh_purchase(self, buyer, product, account, commit=False):
        purchase = PurchaseFactory.get_or_create(buyer, product, account)
        db.session.add(purchase)
        if commit: db.session.commit()
        return purchase

    def _validate_buyer(self, buyer):
        if buyer.is_brazilian():
            if buyer.kind == 'person':
                if not CPFValidator(buyer.document).is_valid():
                    raise InvalidDocumentNumber(buyer.document)
            elif buyer.kind == 'company':
                if not CNPJValidator(buyer.document).is_valid():
                    raise InvalidDocumentNumber(buyer.document)
            if not ZipCodeValidator(buyer.address_zipcode, 'BR').is_valid():
                raise InvalidZipCodeNumber(buyer.address_zipcode)

class PaymentService(object):
    DEFAULT_PROCESSORS = dict(
        pagseguro = PagSeguroPaymentService,
        boleto    = BoletoPaymentService,
        cash      = CashPaymentService,
        promocode = PromoCodePaymentService
    )

    def __init__(self, mailer=None, caravans=None, filters=None, **processors_overrides):
        from segue.caravan.services import CaravanService # THIS IS UGLY
        self.processors_overrides = processors_overrides
        self.mailer               = mailer or MailerService()
        self.caravans             = caravans or CaravanService()
        self.filters              = filters or PaymentFilterStrategies()

    def query(self, by=None, **kw):
        filter_list = self.filters.given(**kw)
        return Payment.query.filter(*filter_list).all()


    def create(self, purchase, method, extra_data):
        if purchase.satisfied: raise PurchaseAlreadySatisfied()
        processor = self.processor_for(method)
        payment = processor.create(purchase, extra_data)
        instructions = processor.process(payment)
        db.session.add(payment)
        db.session.commit()
        return instructions, payment

    def get_one(self, purchase_id, payment_id):
        result = Payment.query.join(Purchase).filter(Purchase.id == purchase_id, Payment.id == payment_id)
        return result.first()

    def conclude(self, purchase_id, payment_id, payload):
        try:
            payment = self.get_one(purchase_id, payment_id)
            if not payment: raise NoSuchPayment(purchase_id, payment_id)
            processor = self.processor_for(payment.type)
            purchase = payment.purchase
            logger.debug('selected processor for conclusion: %s', payment.type)

            transition = processor.conclude(payment, payload)
            payment.recalculate_status()
            purchase.recalculate_status()
            logger.debug('recalculated status: payment.status=%s, purchase.status=%s', payment.status, purchase.status)

            db.session.add(payment)
            db.session.add(transition)
            db.session.add(purchase)
            db.session.commit()
            return purchase
        except KeyError, e:
            logger.error('Exception was thrown while processing payment conclusion! %s', e)
            raise e

    def notify(self, purchase_id, payment_id, payload, source='notification'):
        try:
            payment = self.get_one(purchase_id, payment_id)
            if not payment: raise NoSuchPayment(purchase_id, payment_id)
            processor = self.processor_for(payment.type)
            purchase = payment.purchase
            if purchase.stale: raise PurchaseIsStale()
            logger.debug('selected processor for notification: %s', payment.type)

            transition = processor.notify(purchase, payment, payload, source)
            payment.recalculate_status()
            purchase.recalculate_status()
            logger.debug('recalculated status: payment.status=%s, purchase.status=%s', payment.status, purchase.status)

            db.session.add(payment)
            db.session.add(transition)
            db.session.add(purchase)
            db.session.commit()

            if purchase.satisfied:
                logger.debug('transition is good payment! notifying customer via e-mail!')

                if purchase.product.id == 1:#FIX OMG
                    from segue.purchase.promocode import PromoCodeService
                    from segue.models import Account, Product

                    promo_product = Product.query.filter(Product.id==3).first()#OMG
                    customer=purchase.customer
                    pcs = PromoCodeService()
                    promocode = pcs.create(promo_product, creator=customer, description='Vale ingresso doacao')[0]
                    self.mailer.notify_promocode(customer, promocode)

                elif purchase.product.category == 'donation':
                    document = DocumentService()
                    claim_check = DonationClaimCheckFactory().create(purchase)
                    #TODO: svg_to_pdf return the full path or a tuple
                    doc = document.svg_to_pdf(
                        claim_check.template_file,
                        'claimcheck',
                        claim_check.hash_code,
                        variables=claim_check.template_vars)

                    file_path = document.path_for_filename(os.path.join(config.APP_PATH, 'data'), doc)

                    self.mailer.notify_donation(purchase, payment, file_path)
                else:
                    self.mailer.notify_payment(purchase, payment)

                # TODO: improve this code, caravan concerns should never live here!
                if purchase.kind == 'caravan-rider':
                    logger.debug('attempting to exempt the leader of a caravan')
                    self.caravans.update_leader_exemption(purchase.caravan.id, purchase.caravan.owner)

            return purchase, transition
        except Exception, e:
            logger.error('Exception was thrown while processing payment notification! %s', e)
            raise e

    def processor_for(self, method):
        if method in self.processors_overrides:
            return self.processors_overrides[method]
        if method in self.DEFAULT_PROCESSORS:
            return self.DEFAULT_PROCESSORS[method]()
        raise NotImplementedError(method+' is not a valid payment method')
