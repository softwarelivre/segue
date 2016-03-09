# -*- coding: utf-8 -*-
from datetime import datetime
import os

from segue.core import db, logger, config
from segue.errors import NotAuthorized
from segue.product.errors import NoSuchProduct, ProductExpired
from segue.validation import StudentDocumentValidator

from factories import BuyerFactory, PurchaseFactory
from filters import PurchaseFilterStrategies, PaymentFilterStrategies

from segue.mailer import MailerService

from paypal    import PayPalPaymentService
from pagseguro import PagSeguroPaymentService
from boleto    import BoletoPaymentService
from cash      import CashPaymentService
from models    import Purchase, Payment
from errors    import NoSuchPayment, NoSuchPurchase, PurchaseAlreadySatisfied, PurchaseIsStale, DocumentIsNotDefined, StudentDocumentIsInvalid, StudentDocumentIsNotDefined

from segue.document.services import DocumentService
from segue.purchase.promocode import PromoCodeService, PromoCodePaymentService
from segue.purchase.factories import DonationClaimCheckFactory
from segue.purchase.boleto import BoletoPaymentService
from segue.purchase.boleto.parsers  import BoletoFileParser

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
        buyer    = BuyerFactory().create(buyer_data, schema.buyer)
        if not buyer.document: raise DocumentIsNotDefined()
        if product.category == 'student':
            if not buyer.extra_document and not buyer.document_file_hash:
                raise StudentDocumentIsNotDefined()
            elif buyer.extra_document:
                if not StudentDocumentValidator(buyer.extra_document, account.born_date).is_valid():
                    raise StudentDocumentIsInvalid(buyer.extra_document)

        logger.info("Create buyer: %s", buyer)

        purchase = PurchaseFactory.create(buyer, product, account, **extra)

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

class PaymentService(object):
    DEFAULT_PROCESSORS = dict(
        pagseguro = PagSeguroPaymentService,
        boleto    = BoletoPaymentService,
        cash      = CashPaymentService,
        paypal    = PayPalPaymentService,
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

            self._notify_user(purchase, payment, transition)

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

            self._notify_user(purchase, payment, transition)

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

    def _notify_user(self, purchase, payment, transition):
        if purchase.satisfied and transition.old_status != 'paid' and transition.new_status == 'paid':
            logger.debug('transition is good payment! notifying customer via e-mail!')

            if purchase.product.id == 1:#FIX OMG
                #TODO: REMOVE
                from segue.product.models import Product

                promo_product = Product.query.filter(Product.id==3).first()#OMG
                customer = purchase.customer
                pcs = PromoCodeService()
                promocode = pcs.create(promo_product, creator=customer, description=u'Vale ingresso doação')[0]

                document = DocumentService()
                claim_check = DonationClaimCheckFactory().create(purchase)
                doc = document.svg_to_pdf(
                    claim_check.template_file,
                    'claimcheck',
                    claim_check.hash_code,
                    variables=claim_check.template_vars)[0]

                self.mailer.notify_promocode(customer, promocode, doc)

            elif purchase.product.category == 'donation':
                document = DocumentService()
                claim_check = DonationClaimCheckFactory().create(purchase)

                doc = document.svg_to_pdf(
                    claim_check.template_file,
                    'claimcheck',
                    claim_check.hash_code,
                    variables=claim_check.template_vars)[0]

                self.mailer.notify_donation(purchase, payment, doc)
            else:
                self.mailer.notify_payment(purchase, payment)

            # TODO: improve this code, caravan concerns should never live here!
            if purchase.kind == 'caravan-rider':
                logger.debug('attempting to exempt the leader of a caravan')
                self.caravans.update_leader_exemption(purchase.caravan.id, purchase.caravan.owner)

class ProcessBoletosService(object):

    def __init__(self, boleto_service=None, boleto_parser=None, payment_service=None):
        self.boleto_service = boleto_service or BoletoPaymentService()
        self.payment_service = payment_service or PaymentService()
        self.boleto_parser = boleto_parser or BoletoFileParser()

    def process(self, data):
        good_payments = []
        late_payments = []
        bad_payments = []
        unknown_payments = []

        for entry in self.boleto_parser.parse(data):

            payment = self.boleto_service.get_by_our_number(entry.get('our_number'))
            if not payment:
                unknown_payments.append(entry)
                continue

            print payment.purchase
            if entry['payment_date'] > payment.legal_due_date:
                late_payments.append(dict(entry=entry, payment=payment))
            else:
                purchase, transition = self.payment_service.notify(payment.purchase.id, payment.id, entry, 'script')

                if transition.errors:
                    bad_payments.append(dict(entry=entry, payment=payment, errors=transition.errors))
                else:
                    good_payments.append(dict(entry=entry, payment=payment, purchase=purchase))

        #TODO: MAKE A RESPONSE
        return {'good': good_payments,
                'late': late_payments,
                'bad': bad_payments,
                'unknown': unknown_payments}
