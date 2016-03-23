# -*- coding: utf-8 -*-

from segue.errors import ExternalServiceError
from segue.purchase.errors import InvalidPaymentNotification
from segue.core import db, logger, config

from .factories import PayPalPaymentFactory, PayPalTransitionFactory, PaypalDetailsFactory

from paypal import PayPalAPIResponseError, PayPalInterface, PayPalConfig


class PayPalPaymentService(object):
    def __init__(self, session=None, factory=None):
        pass
        self.session = session or PayPalSession()
        self.factory  = factory  or PayPalPaymentFactory()

    def create(self, purchase, data=None):
        payment = self.factory.create(purchase, data=data)
        db.session.add(payment)
        db.session.commit()
        return payment

    def process(self, payment):
        try:
            logger.debug('starting paypal checkout for %s...', payment.id)
            response = self.session.start_express_checkout(payment)
            logger.debug('Paypal answered with response... %s', response)

            if response.success:
                payment.token = response.token
                payment.correlation_id = response.correlationid
                url = self.session.build_instructions(payment.token)
                logger.debug('Completed checkout for %s. result is: %s', payment.id, url)
                return dict(redirectUserTo=url)
            else:
                logger.error('Error while processing the payment %s response:', payment.id, response)
                raise ExternalServiceError('paypal')

        except PayPalAPIResponseError as e:
            raise ExternalServiceError('paypal')

    def notify(self, purchase, payment, payload=None, source='notification'):
        logger.debug('Received paypal direct notification with payload %s', payload)
        token = payload.get('token', None)
        payer_id = payload.get('PayerID', None)

        if not token or not payer_id or not hasattr(payment, "token"):
            raise InvalidPaymentNotification()

        checkout_details = self.session.get_express_checkout_details(token=token)

        transition = PayPalTransitionFactory.create(payment=payment, payload=checkout_details, source=source)

        if transition.new_status == 'pending':
            db.session.add(transition)
            logger.info('Started do_express_checkout')
            response = self.session.do_express_checkout(payment, payload)
            logger.info('Response do_express_checkout with %s', response)

        return transition

    def conclude(self, payment, payload=None):
        logger.debug('Received paypal conclude notification with payload %s', payload)
        token = payload.get('token', None)

        if not token or not hasattr(payment, "token"):
            raise InvalidPaymentNotification()

        checkout_details = self.session.get_express_checkout_details(token=token)
        return PayPalTransitionFactory.create(payment=payment, payload=checkout_details, source='conclude')


class PayPalSession(object):

    def __init__(self, paypal_config=None, details_factory=None):
        self.paypal_config = paypal_config or PayPalSession.default_config()
        self.interface = PayPalInterface(config=self.paypal_config)
        self.factory = details_factory or PaypalDetailsFactory()

    @staticmethod
    def default_config():
        return PayPalConfig(
                    API_ENVIRONMENT=config.PAYPAL_API_ENVIRONMENT,
                    API_USERNAME=config.PAYPAL_API_USERNAME,
                    API_PASSWORD=config.PAYPAL_API_PASSWORD,
                    API_SIGNATURE=config.PAYPAL_API_SIGNATURE)

    def start_express_checkout(self, payment):
        checkout = self.factory.create_set_express_checkout(payment)
        return self.interface.set_express_checkout(**checkout)

    def get_express_checkout_details(self, token):
        checkout_details = self.interface.get_express_checkout_details(token=token)
        if not checkout_details.success:
                raise IndentationError('Error while getting express checkout details %', checkout_details)
        return checkout_details

    def do_express_checkout(self, payment, payload):
        payer_id = payload['PayerID']
        checkout = self.factory.create_do_express_checkout(payment, payer_id)
        return self.interface.do_express_checkout_payment(**checkout)

    def build_instructions(self, token):
        url = self.interface.generate_express_checkout_redirect_url(token)
        return url + '&useraction=commit'