# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
from sqlalchemy import and_
import os
import xmltodict
import dateutil.parser
import collections


from segue.core import db, logger, config
from segue.errors import NotAuthorized
from segue.product.errors import NoSuchProduct, ProductExpired
from segue.validation import StudentDocumentValidator

from factories import BuyerFactory, PurchaseFactory
from filters import PurchaseFilterStrategies, PaymentFilterStrategies

from segue.mailer import MailerService

from paypal    import PayPalPaymentService
from pagseguro import PagSeguroPaymentService
from cash      import CashPaymentService
from models    import Purchase, Payment
from errors    import *

from segue.purchase.promocode import PromoCodeService, PromoCodePaymentService, PromoCode
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
    def __init__(self, db_impl=None, mailer=None, payments=None, filters=None, deadline=None, promocode=None):
        self.db = db_impl or db
        self.payments = payments or PaymentService()
        self.filters = filters or PurchaseFilterStrategies()
        self.deadline = deadline or OnlinePaymentDeadline()
        self.promocode_service = promocode or PromoCodeService()
        self.mailer = mailer or MailerService()

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

        #TODO: REVIEW
        if product.category == 'student':
            if not buyer.extra_document and not buyer.document_file_hash:
                raise StudentDocumentIsNotDefined()
            elif buyer.extra_document:
                if not StudentDocumentValidator(buyer.extra_document, account.born_date).is_valid():
                    raise StudentDocumentIsInvalid(buyer.extra_document)

        logger.info("Create buyer: %s", buyer)

        #TODO: REVIEW
        survey = {}
        if 'shirt_size' in buyer_data and 'delivery' in buyer_data:
            survey = {
                'shirt_size': extra.pop('shirt_size', None),
                'delivery': extra.pop('delivery', None)
            }

        purchase = PurchaseFactory.create(buyer, product, account, **extra)

        self.db.session.add(buyer)
        self.db.session.add(purchase)

        if purchase.category == 'government':
            self.mailer.notify_gov_purchase(purchase)

        if 'hash_code' in buyer_data:
            hash = str(buyer_data['hash_code'])
            _, payment = self.payments.create(purchase, 'promocode', {'hash_code': hash})

            #TODO: REVIEW
            if payment.status == 'paid':
                promocode = PromoCode.query.filter(PromoCode.hash_code == hash).first()

                if product.category == 'corporate-promocode' or product.category == 'gov-promocode':
                    account.corporate_id = promocode.creator.corporate_owned.id
                    self.db.session.add(account)
                    self.mailer.notify_corporate_promocode_payment(purchase, promocode)

                elif promocode.discount == 1.0:
                    self.mailer.notify_payment(purchase)



        if commit:
            self.db.session.commit()

        #TODO: REVIEW
        if survey:
            from segue.survey.services import SurveyService
            survey_name = 'fisl17_donation_shirt_purchase_{}'.format(purchase.id)

            service = SurveyService()
            service.save_answers(survey_name, survey, by_user=account)


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
        return self.promocode_service.check(hash, by=by)

    def give_ticket(self, account, product, commit=True):
        purchase = PurchaseFactory.get_or_create(None, product, account)
        purchase.status = 'paid'
        purchase.amount = 0
        purchase.qty = 1
        db.session.add(purchase)
        if commit: db.session.commit()
        return purchase

    def give_volunteer_ticket(self, account, commit=True):
        from segue.product.models import VolunteerProduct
        product = VolunteerProduct.query.first()
        return self.give_ticket(account, product, commit=commit)

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

    def lookup(self, criteria=None, by=None, limit=0):
        base = Purchase.query.join('customer').join('product')
        filters = self.filters.given_criteria(**criteria)
        queryset = base.filter(and_(*filters))

        if limit:
            queryset = queryset.limit(limit)

        return queryset.all()

class PaymentService(object):
    DEFAULT_PROCESSORS = dict(
        pagseguro = PagSeguroPaymentService,
        boleto    = BoletoPaymentService,
        cash      = CashPaymentService,
        paypal    = PayPalPaymentService,
        promocode = PromoCodePaymentService
    )

    def __init__(self, mailer=None, caravans=None, filters=None, promocodes=None, **processors_overrides):
        from segue.caravan.services import CaravanService
        self.processors_overrides = processors_overrides
        self.mailer               = mailer or MailerService()
        self.caravans             = caravans or CaravanService()
        self.filters              = filters or PaymentFilterStrategies()
        self.promocodes           = promocodes or PromoCodeService()

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

            if purchase.satisfied:
                if transition.old_status != 'paid' and transition.new_status == 'paid':
                    self.on_finish_payment(purchase)

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
                if transition.old_status != 'paid' and transition.new_status == 'paid':
                    self.on_finish_payment(purchase)
            elif purchase.category == 'student':
                if purchase.status == 'student_document_in_analysis':
                   self.mailer.notify_student_purchase_received(purchase)

            return purchase, transition
        except Exception, e:
            logger.error('Exception was thrown while processing payment notification! %s', e)
            raise e

    def on_finished_student_document_analysis(self, purchase):
        if purchase.category != 'student':
            # TODO: THROW A EXCEPTION
            return {}

        if purchase.payment_analysed() == 'paid':
            db.session.add(purchase)
            db.session.commit()
            self.mailer.notify_student_document_analyzed(purchase)
            return True
        else:
            return False


    def on_gov_document_received(self, purchase, document_file_hash):
        if purchase.category != 'government' and purchase.status == 'gov_document_submission_pending':
            #TODO: THROW A EXCEPTION
            return {}
        else:
            purchase.buyer.document_file_hash = document_file_hash
            purchase.status = 'gov_document_in_analysis'
            db.session.add(purchase)
            db.session.commit()
            self.mailer.notify_gov_purchase_received(purchase)


    def on_gov_document_analyzed(self, purchase):
        if purchase.category != 'government' and purchase.status == 'gov_document_in_analysis':
            #TODO: THROW A EXCEPTION
            return False
        else:
            purchase.status = 'pending'
            db.session.add(purchase)
            db.session.commit()
            self.on_finish_governament(purchase)
            return True


    def on_finish_payment(self, purchase):
        if purchase.category == 'business':
            self.on_finish_corporate(purchase)
        elif purchase.category == 'government':
            pass
        elif purchase.category == 'donation':
            if purchase.product.gives_promocode:
                self.on_finish_promocode_donation(purchase)
            else:
                self.on_finish_normal_donation(purchase)
        elif purchase.kind == 'caravan-rider':
            self.on_finish_caravan_rider(purchase)
        else:
            self.mailer.notify_payment(purchase)

    def on_finish_corporate(self, purchase):
        from segue.product.models import Product
        promo_product = Product.query.filter(Product.id==purchase.product.promocode_product_id).first()

        data = {
            'description': promo_product.description,
            'discount': 1.0,
            'product_id': purchase.product.promocode_product_id,
            'start_at': datetime.now().strftime("%d/%m/%Y"),
            'end_at': (datetime.now() + timedelta(days=128)).strftime("%d/%m/%Y")
        }

        promocodes = self.promocodes.create(
            data,
            creator=purchase.customer,
            quantity=purchase.qty)

        self.mailer.notify_corporate_payment(purchase, promocodes)

    def on_finish_governament(self, purchase):
        from segue.product.models import Product
        promo_product = Product.query.filter(Product.id == purchase.product.promocode_product_id).first()

        data = {
            'description': promo_product.description,
            'discount': 1.0,
            'product_id': purchase.product.promocode_product_id,
            'start_at': datetime.now().strftime("%d/%m/%Y"),
            'end_at': (datetime.now() + timedelta(days=128)).strftime("%d/%m/%Y")
        }

        promocodes = self.promocodes.create(
            data,
            quantity=purchase.qty,
            creator=purchase.customer)

        self.mailer.notify_gov_purchase_analysed(purchase, promocodes)

    def on_finish_promocode_donation(self, purchase):
        from segue.product.models import Product
        promo_product = Product.query.filter(Product.id==purchase.product.promocode_product_id).first()

        data = {
            'description': promo_product.description,
            'discount': 1.0,
            'product_id': purchase.product.promocode_product_id,
            'start_at': datetime.now().strftime("%d/%m/%Y"),
            'end_at': (datetime.now() + timedelta(days=128)).strftime("%d/%m/%Y")
        }

        promocodes = self.promocodes.create(
            data,
            quantity=purchase.qty,
            creator=purchase.customer
        )
        document,_ = ClaimCheckDocumentService().create(purchase)
        self.mailer.notify_promocode(purchase.customer, promocodes[0], document)

    def on_finish_normal_donation(self, purchase):
        document = ClaimCheckDocumentService().create(purchase)[0]
        self.mailer.notify_donation(purchase, document)

    def on_finish_caravan_rider(self, purchase):
        from segue.caravan.models import Caravan
        logger.debug('attempting to exempt the leader of a caravan')
        #TODO: FIX ME
        caravan = Caravan.query.filter(Caravan.id==purchase.caravan_id).first()
        self.mailer.notify_payment(purchase)
        self.caravans.update_leader_exemption(caravan.id, caravan.owner)

    def processor_for(self, method):
        if method in self.processors_overrides:
            return self.processors_overrides[method]
        if method in self.DEFAULT_PROCESSORS:
            return self.DEFAULT_PROCESSORS[method]()
        raise NotImplementedError(method+' is not a valid payment method')


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


class ClaimCheckDocumentService(object):

    def __init__(self, documents=None, claim_check_factory=None):
        from segue.purchase.factories import DonationClaimCheckFactory
        from segue.document.services import DocumentService
        self.documents = documents or DocumentService()
        self.claim_check_factory = claim_check_factory or DonationClaimCheckFactory()

    def create(self, purchase):
        claim_check = self.claim_check_factory.create(purchase)

        return self.documents.svg_to_pdf(
            claim_check.template_file,
            'claimcheck',
            claim_check.hash_code,
            variables=claim_check.template_vars
        )


class AdempiereService(object):

    def __init__(self):
        pass

    def generate_report(self, initial_date, end_date):
        #TODO: FIX THIS IMPORT
        from segue.models import Product

        dataset = []

        exclude_categories = ['donation']
        purchases = Purchase.query \
            .join('product') \
            .filter(Purchase.status == 'paid') \
            .filter(Product.category.notin_(exclude_categories)) \
            .order_by(Purchase.id) \
            .all()

        for purchase in purchases:
            account = purchase.customer
            buyer = purchase.buyer

            finished_payments = [payment for payment in purchase.payments if
                                 (payment.status in Payment.VALID_PAYMENT_STATUSES)]

            paid_amount = purchase.total_amount
            payments = []
            for payment in finished_payments:
                if hasattr(payment, 'promocode') and payment.promocode:
                    paid_amount -= payment.paid_amount
                else:
                    payments.append(payment)

            # free fries = exclude from report
            if not paid_amount:
                continue

            if len(payments) > 1:
                continue

            transaction_date = self._get_transition_date(payments[0])
            transaction = datetime(transaction_date.year, transaction_date.month, transaction_date.day)

            if not (initial_date <= transaction < end_date):
                continue


            #FORMAT THE STUFFF
            purchase_discount = '0'
            purchase_category = self._get_category(purchase.product.category)
            from segue.purchase.factories import BuyerFactory
            if not buyer:
                buyer = BuyerFactory().from_account(account)

            buyer_type = 'nulo'
            buyer_name = buyer.name
            buyer_cpf = self._format_document(buyer.document) or 'nulo'
            buyer_cnpj = self._format_document(buyer.document, type='CNPJ') or 'nulo'

            buyer_phone = buyer.contact
            buyer_address_zipcode = buyer.address_zipcode

            if buyer_cnpj != 'nulo':
                buyer_type = 'PJ'
                buyer_phone = self._format_phone(buyer.contact)
                buyer_address_zipcode = self._format_cep(buyer.address_zipcode)

            if buyer_cpf != 'nulo':
                buyer_type = 'PF'
                buyer_name = buyer_name.title()
                buyer_phone = self._format_phone(buyer.contact)
                buyer_address_zipcode = self._format_cep(buyer.address_zipcode)

            if buyer_cpf == 'nulo' and buyer_cnpj == 'nulo':
                buyer_type = 'EX'
                buyer_name = buyer_name.title()

            data = collections.OrderedDict()
            data['purchase_id'] = purchase.id

            data['buyer_type'] = buyer_type

            data['buyer_cpf'] = buyer_cpf
            data['buyer_cnpj'] = buyer_cnpj

            data['buyer_name'] = buyer_name
            data['buyer_email'] = account.email
            data['buyer_phone1'] = buyer_phone
            data['buyer_phone2'] = 'nulo'
            data['buyer_address_zipcode'] = buyer_address_zipcode
            data['buyer_address_country'] = buyer.address_country
            data['buyer_address_state'] = buyer.address_state.upper()
            data['buyer_address_city'] = buyer.address_city
            data['buyer_address_street'] = buyer.address_street
            data['buyer_address_number'] = buyer.address_number
            data['buyer_address_neighborhood'] = buyer.address_neighborhood
            data['buyer_address_extra'] = buyer.address_extra or 'nulo',

            data['purchase_qty'] = purchase.qty
            data['purchase_amount'] = '{0:.2f}'.format(paid_amount)
            data['purchase_discount'] = purchase_discount
            data['purchase_description'] = self._get_description(purchase_category,
                                                                 self._get_payment_type(payments[0]),
                                                                 purchase.qty,
                                                                 purchase.id,
                                                                 transaction_date)

            dataset.append(data)

        return dataset

    def _format_phone(self, value):
        if len(value) < 10:
            return 'nulo'

        suffix_len = len(value) - 2
        f = '{}{}-' + '{}' * suffix_len

        return f.format(*list(value))

    def _format_cep(self, value):
        # possibilites:
        # None
        # formatted
        # not formatted
        if len(value) == 9:
            return value
        if len(value) == 8:
            return "{}{}{}{}{}-{}{}{}".format(*list(value))
        else:
            return 'nulo'

    def _format_document(self, value, type="CPF"):
        # possibilites:
        # None
        # formatted
        # not formatted
        if type == "CPF" and value and len(value) == 11:
            return "{}{}{}.{}{}{}.{}{}{}-{}{}".format(*list(value))
        elif type == 'CNPJ' and len(value) == 14:
            return "{}{}.{}{}{}.{}{}{}/{}{}{}{}-{}{}".format(*list(value))
        else:
            return "nulo"


    def _get_payment_type(self, payment):
        if payment.type == 'boleto':
            return 'Boleto'
        elif payment.type == 'pagseguro':
            return 'PagSeguro'
        elif payment.type == 'paypal':
            return 'PayPal'
        else:
            return ''


    def _get_description(self, category, payment_type, quantity, number, transaction_date):
        first_paragraph = '{:0>2d} inscrição categoria {} para o 18º Fórum Internacional Software Livre, a realizar-se de 05 a 08 de julho de 2017, no Centro de Eventos da PUC, em Porto Alegre/RS. * * *'.format(quantity, category)
        second_paragraph = 'Inscrição nº {}. * * *'.format(number)
        third_paragraph = ' {} * * *. A Associação Software Livre.Org declara para fins de não incidência na fonte do IRPJ, da CSLL, da COFINS e da contribuição para PIS/PASEP ser associação sem fins lucrativos, conforme art. 64 da Lei nº 9.43 0/1996 e atualizações e Instrução Normativa RFB nº 1.234/2012. * * *'.format(payment_type)
        forth_paragraph = 'Tributos: ISS 5% + COFINS 7,6% = 12,6%.'
        fifth_paragraph = ' * * *. Recebido em: {}'.format(transaction_date.strftime('%d-%m-%Y'))
        text = first_paragraph + second_paragraph + third_paragraph + forth_paragraph + fifth_paragraph
        return text

    def _get_transition_date(self, payment):
        transition = [transition for transition in payment.transitions
                      if (transition.new_status in Payment.VALID_PAYMENT_STATUSES and
                          transition.old_status not in Payment.VALID_PAYMENT_STATUSES)][0]
        if payment.type == 'paypal':
            return transition.created
        if payment.type == 'pagseguro':
            return self._get_date_pagseguro(transition)
        elif payment.type == 'boleto':
            if hasattr(transition, 'payment_date'):
                return transition.payment_date
            else:
                return transition.created
        else:
            return transition.created

    def _get_category(self, name):
        if name == 'normal' or name == 'proponent':
            return 'individual'
        elif name == 'student' or name == 'proponent-student':
            return 'estudante'
        elif name == 'promocode':
            return 'individual'
        elif name == 'caravan':
            return 'caravanista'
        elif name == 'caravan-rider':
            return 'caravana'
        elif name == 'business':
            return 'corporativa'
        elif name == 'government':
            return 'empenho'
        elif name == 'foreigner':
            return 'estrangeiro'
        else:
            return "Tipo de ingresso desconhecido"

    def _get_date_pagseguro(self, transition):
        pagseguro_data = xmltodict.parse(transition.payload)
        date = dateutil.parser.parse(pagseguro_data['transaction']['lastEventDate'])
        naive = date.replace(tzinfo=None)
        return naive

    def _get_our_number(self, payment):
        return payment.our_number if getattr(payment, 'our_number', None) is not None else ''
