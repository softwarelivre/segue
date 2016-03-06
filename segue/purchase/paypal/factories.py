# -*- coding: utf-8 -*-

from paypal import PayPalConfig

from segue.core import config, logger

from segue.purchase.factories import PaymentFactory, TransitionFactory
from segue.purchase.errors import InvalidPaymentNotification

from models import PayPalPayment, PayPalPaymentTransition


class PayPalPaymentFactory(PaymentFactory):
    model = PayPalPayment

    def __init__(self):
        pass

    def create(self, purchase, data=None):
        payment = super(PayPalPaymentFactory, self).create(purchase, target_model=self.model, extra_data=data)
        payment.invnum = "A{0:05d}PU{1:05d}".format(purchase.customer.id, purchase.id)
        return payment


class PaypalDetailsFactory(object):

    DISABLESHIPPING = 1
    PAYMENTACTION = 'Sale'
    CURRENCYCODE = 'BRL'

    def create_item_details(self, purchase):
        return {
            'L_PAYMENTREQUEST_0_NAME0': purchase.product.description,
            'L_PAYMENTREQUEST_0_QTY0': 1,
            'L_PAYMENTREQUEST_0_AMT0': purchase.amount,
            'L_PAYMENTREQUEST_0_NUMBER0': purchase.product.id
        }

    def create_payment_details(self, payment):
        return {
            'PAYMENTREQUEST_0_CURRENCYCODE': self.__class__.CURRENCYCODE,
            'PAYMENTREQUEST_0_PAYMENTACTION': self.__class__.PAYMENTACTION,
            'PAYMENTREQUEST_0_AMT': payment.amount,
            'PAYMENTREQUEST_0_ITEMAMT': payment.amount,
            'PAYMENTREQUEST_0_INVNUM': payment.invnum
        }

    def create_request_details(self, payment):
        return {
            'EMAIL': payment.purchase.customer.email,
            'RETURNURL': self.return_url(payment, payment.purchase),
            'CANCELURL': self.cancel_url(),
            'NOSHIPPING': self.__class__.DISABLESHIPPING
        }

    def create_do_express_checkout(self, payment, payer_id):
        return {
            'AMT': payment.amount,
            'PAYMENTACTION': self.__class__.PAYMENTACTION,
            'CURRENCYCODE': self.__class__.CURRENCYCODE,
            'PAYERID': payer_id,
            'TOKEN': payment.token
        }

    def return_url(self, payment, purchase):
        return '{}/api/purchases/{}/payments/{}/paypal/notify'.format(config.BACKEND_URL, purchase.id, payment.id)

    def cancel_url(self):
        return '{}/#/home'.format(config.FRONTEND_URL)

    def create_set_express_checkout(self, payment):
        item_details = self.create_item_details(payment.purchase)
        payment_details = self.create_payment_details(payment)
        request_details = self.create_request_details(payment)

        data = {}
        data.update(item_details)
        data.update(payment_details)
        data.update(request_details)
        return data


class PayPalTransitionFactory(TransitionFactory):
    model = PayPalPaymentTransition

    PAYPAL_STATUSES = {
        'PaymentActionNotInitiated': 'pending', 'PaymentActionFailed': 'failed',
        'PaymentActionInProgress': 'in analysis', 'PaymentActionCompleted': 'paid'
    }

    @classmethod
    def parse_payload(cls, payment, payload):
        cls.check_invoicenum(payment, payload)
        resolved_status = cls.PAYPAL_STATUSES.get(payload['CHECKOUTSTATUS'], 'unknown')
        return resolved_status

    @classmethod
    def check_invoicenum(cls, payment, payload):
        if payment.token != payload['TOKEN']:
            raise InvalidPaymentNotification('Invalid Token')
        if payment.invnum != payload['PAYMENTREQUEST_0_INVNUM']:
            raise InvalidPaymentNotification('Invoice number does not match')

    @classmethod
    def create(cls, payment, payload, source):
        status = cls.parse_payload(payment, payload)

        transition = TransitionFactory.create(payment, source, target_model=cls.model)
        transition.new_status        = status
        transition.payload           = str(payload)
        return transition
