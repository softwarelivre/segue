from segue.factory import Factory

import schema
from models import Buyer, Purchase, Payment, Transition, ExemptPurchase

class BuyerFactory(Factory):
    model = Buyer

    CREATE_WHITELIST = schema.buyer["properties"].keys()

    @classmethod
    def clean_for_insert(cls, data):
        data = { c:v for c,v in data.items() if c in BuyerFactory.CREATE_WHITELIST }
        return data;

class PurchaseFactory(Factory):
    QUERY_WHITELIST = ('customer_id',)
    model = Purchase

    @classmethod
    def create(cls, buyer, product, account, **extra_fields):
        effective_class = product.special_purchase_class() or cls.model
        result = effective_class(**extra_fields)
        result.buyer = buyer
        result.product = product
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
        #FIX ME product is from database
        from segue.core import logger
        product = purchase.product
        if product.category == 'donation' and product.price == 0:
            if extra_data and 'amount' in extra_data:
                amount = int(extra_data['amount'])
                if amount >= 10:
                    payment.amount = amount
                else:
                    amount = 0
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
