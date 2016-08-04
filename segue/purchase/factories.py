from segue.factory import Factory
from segue.hasher import Hasher
from segue.document.services import DocumentService

import schema
from datetime import datetime, timedelta
from models import Buyer, Purchase, Payment, Transition, ExemptPurchase, ClaimCheck

class BuyerFactory(Factory):
    model = Buyer

    def __init__(self, document_service=None, hash=None):
        self.document_service = document_service or DocumentService()
        self.hash = hash or Hasher(10)

    def create(self, data, schema):
        #TODO: CREATE A CONSTANT FOR DOCUMENT KIND
        file_payload = data.get('document_file', None)
        document_file_hash = None
        if file_payload:
            document_file_hash = self.hash.generate()
            self.document_service.base64_to_pdf('buyer-document', document_file_hash, file_payload)
        buyer = BuyerFactory.from_json(data, schema)
        buyer.document_file_hash = document_file_hash
        return buyer

    def from_account(self, account):
        buyer = Buyer()
        #TODO: CHECK BUYER KIND
        if account.has_role('user'):
            buyer.kind = 'person'
        elif account.has_role('corporate'):
            buyer.kind = 'company'
        elif account.has_role('foreign'):
            buyer.kind = 'foreign'

        buyer.name                 = account.name
        buyer.document             = account.document
        buyer.contact              = account.phone
        buyer.address_city         = account.city
        buyer.address_country      = account.country
        buyer.address_state        = account.address_state
        buyer.address_street       = account.address_street
        buyer.address_neighborhood = account.address_neighborhood
        buyer.address_number       = account.address_number
        buyer.address_extra        = account.address_extra
        buyer.address_zipcode      = account.address_zipcode

        return buyer
    @classmethod
    def clean_for_insert(cls, data):
        data.pop('document_file', None)
        cpf = data.pop('cpf', None)
        cnpj = data.pop('cnpj', None)
        passport = data.pop('passport', None)
        data['document'] = cpf or cnpj or passport
        return data

class PurchaseFactory(Factory):
    QUERY_WHITELIST = ('customer_id',)
    model = Purchase

    @classmethod
    def create(cls, buyer, product, account, **extra_fields):
        effective_class = product.special_purchase_class() or cls.model
        result = effective_class(**extra_fields)
        result.buyer = buyer
        result.product = product
        result.due_date = product.due_date
        #TODO: FIX LATER
        if result.status == 'gov_document_submission_pending' and buyer.document_file_hash:
            result.status = 'gov_document_in_analysis'
        #TODO: IMPROVE CALCULATE THE AMOUNT OF THE PURCHASE
        if not result.amount:
            result.amount = product.price
        result.customer = account
        return result

    @classmethod
    def get_or_create(cls, buyer, product, account, **extra_fields):
        effective_class = product.special_purchase_class() or cls.model
        existing_purchase = effective_class.query.filter(Purchase.product == product, Purchase.customer == account, Purchase.status == 'pending').first()
        if existing_purchase:
            existing_purchase.buyer = buyer
            return existing_purchase
        else:
            return cls.create(buyer, product, account, **extra_fields)

class PaymentFactory(Factory):
    model = Payment

    def __init__(self):
        pass

    def create(self, purchase, target_model=Payment, extra_data=None):
        payment = target_model()
        payment.purchase = purchase
        payment.amount   = purchase.outstanding_amount
        payment.due_date = purchase.due_date
        return payment


class TransitionFactory(Factory):
    model = Transition

    @classmethod
    def create(cls, payment, source, target_model=Transition):
        transition = target_model()
        transition.payment = payment
        transition.source = source
        transition.old_status = payment.status
        return transition

class DonationClaimCheckFactory(Factory):

    def __init__(self, hasher=None):
        self.hasher = hasher or Hasher(10)

    def create(self, purchase):
        date = datetime.now()
        hash_code = self.hasher.generate()
        return ClaimCheck(purchase, date=date, hash_code=hash_code)
