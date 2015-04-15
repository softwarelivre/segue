from datetime import timedelta, datetime
import mockito

from segue.purchase.factories import PaymentFactory
from segue.purchase.services import PurchaseService, PaymentService
from segue.purchase.models import Payment
from segue.purchase.pagseguro.models import PagSeguroPayment
from segue.errors import NotAuthorized, PaymentVerificationFailed, ProductExpired, \
                         InvalidPaymentNotification, NoSuchPayment, NoSuchProduct, \
                         PurchaseAlreadySatisfied

from ..support import SegueApiTestCase, hashie
from ..support.factories import *

class DummyPayment(Payment):
    __mapper_args__ = { 'polymorphic_identity': 'dummy' }

class PurchaseServiceTestCases(SegueApiTestCase):
    def setUp(self):
        super(PurchaseServiceTestCases, self).setUp()
        self.service = PurchaseService()

    def test_listing_purchases(self):
        customer = self.create_from_factory(ValidAccountFactory)
        p1 = self.create_from_factory(ValidPurchaseFactory, customer=customer)
        p2 = self.create_from_factory(ValidPurchaseFactory, customer=customer)

        result = self.service.query(by=customer)

        self.assertEquals(len(result), 2)

    def test_purchasing_a_product(self):
        account    = self.create_from_factory(ValidAccountFactory)
        product    = self.create_from_factory(ValidProductFactory)
        buyer_data = self.build_from_factory(ValidBuyerPersonFactory).to_json()

        result = self.service.create(buyer_data, product, account)

        self.assertEquals(result.customer, account)
        self.assertEquals(result.product, product)
        self.assertEquals(result.status, 'pending')
        self.assertEquals(result.buyer.name, buyer_data['name'])
        self.assertEquals(result.buyer.kind, buyer_data['kind'])
        self.assertEquals(result.buyer.address_street,  buyer_data['address_street'])
        self.assertEquals(result.buyer.address_number,  buyer_data['address_number'])
        self.assertEquals(result.buyer.address_extra,   buyer_data['address_extra'])
        self.assertEquals(result.buyer.address_city,    buyer_data['address_city'])
        self.assertEquals(result.buyer.address_country, buyer_data['address_country'])
        self.assertEquals(result.buyer.address_zipcode, buyer_data['address_zipcode'])

    def test_purchasing_a_caravan_product(self):
        account    = self.create_from_factory(ValidAccountFactory)
        product    = self.create_from_factory(ValidCaravanProductFactory)
        caravan    = self.create_from_factory(ValidCaravanFactory)
        buyer_data = self.build_from_factory(ValidBuyerPersonFactory).to_json()
        buyer_data['caravan_invite_hash'] = '123XXX'

        result = self.service.create(buyer_data, product, account, caravan=caravan)

        self.assertEquals(result.customer, account)
        self.assertEquals(result.product, product)
        self.assertEquals(result.status, 'pending')
        self.assertEquals(result.buyer.name, buyer_data['name'])
        self.assertEquals(result.buyer.kind, buyer_data['kind'])
        self.assertEquals(result.kind, 'caravan-rider')
        self.assertEquals(result.caravan, caravan)


    def test_retrieving_a_purchase(self):
        other_account = self.create_from_factory(ValidAccountFactory)
        purchase      = self.create_from_factory(ValidPurchaseFactory)

        result = self.service.get_one(purchase.id, by=purchase.customer)
        self.assertEquals(result.id, purchase.id)

        with self.assertRaises(NotAuthorized):
            self.service.get_one(purchase.id, by=other_account)

    def test_cannot_create_a_payment_for_purchase_of_an_expired_product(self):
        yesterday = datetime.now() - timedelta(days=1)
        product = self.create_from_factory(ValidProductFactory, sold_until=yesterday)
        purchase = self.create_from_factory(ValidPurchaseFactory, product=product)

        with self.assertRaises(ProductExpired):
            self.service.create_payment(purchase.id, 'dummy', {}, by=purchase.customer)

    def test_clone_a_purchase(self):
        yesterday = datetime.now() - timedelta(days=1)
        tomorrow  = datetime.now() + timedelta(days=1)
        product1 = self.create_from_factory(ValidProductFactory, kind="ticket", category='normal',  sold_until=yesterday)
        product2 = self.create_from_factory(ValidProductFactory, kind="ticket", category='normal',  sold_until=tomorrow)
        product3 = self.create_from_factory(ValidProductFactory, kind="ticket", category='student', sold_until=tomorrow)

        purchase1 = self.create_from_factory(ValidPurchaseFactory, product=product1)
        purchase2 = self.create_from_factory(ValidPurchaseFactory, product=product2)
        purchase3 = self.create_from_factory(ValidPurchaseFactory, product=product2, status='paid')

        result = self.service.clone_purchase(purchase1.id, by=purchase1.customer)
        self.assertEquals(result.product.sold_until, tomorrow)
        self.assertEquals(result.buyer, purchase1.buyer)
        self.assertEquals(result.customer, purchase1.customer)
        self.assertEquals(result.product, product2)

        result = self.service.clone_purchase(888, by=purchase2.customer)
        self.assertRaises(result, None)

        with self.assertRaises(NotAuthorized):
            self.service.clone_purchase(purchase1.id, by=purchase2.customer)

        with self.assertRaises(NoSuchProduct):
            self.service.clone_purchase(purchase2.id, by=purchase2.customer)

        with self.assertRaises(PurchaseAlreadySatisfied):
            self.service.clone_purchase(purchase3.id, by=purchase3.customer)



class PaymentServiceTestCases(SegueApiTestCase):
    def setUp(self):
        super(PaymentServiceTestCases, self).setUp()
        self.dummy = mockito.Mock()
        self.mailer = mockito.Mock()
        self.service = PaymentService(mailer=self.mailer, dummy=self.dummy)

    def test_creating_a_payment_delegates_creation_and_processing_to_correct_payment_implementation(self):
        data = dict(got='mock?')
        instructions = dict(got='result?')
        purchase = self.create_from_factory(ValidPurchaseFactory)
        payment = self.build_from_factory(ValidPaymentFactory)

        mockito.when(self.dummy).create(purchase, data).thenReturn(payment)
        mockito.when(self.dummy).process(payment).thenReturn(instructions)

        result = self.service.create(purchase, 'dummy', data)

        self.assertEquals(result, instructions)

    def test_cannot_create_a_payment_for_a_satisfied_purchase(self):
        purchase = self.create_from_factory(ValidPurchaseFactory, status='paid')

        with self.assertRaises(PurchaseAlreadySatisfied):
            self.service.create(purchase, 'dummy', {})

    def test_retrieves_one_payment_autocasted_to_its_type(self):
        purchase = self.create_from_factory(ValidPurchaseFactory)

        p1 = self.create_from_factory(ValidPaymentFactory, purchase=purchase)
        p2 = self.create_from_factory(ValidPaymentFactory, purchase=purchase, type='pagseguro')
        p1_id, p2_id = self.db_expunge(p1, p2)

        retrieved = self.service.get_one(purchase.id, p1_id)
        self.assertEquals(retrieved.id, p1_id)
        self.assertEquals(retrieved.__class__, Payment)

        retrieved = self.service.get_one(purchase.id, p2_id)
        self.assertEquals(retrieved.id, p2_id)
        self.assertEquals(retrieved.__class__, PagSeguroPayment)

    def test_notification_that_pays_the_balance_of_purchase(self):
        payload    = mockito.Mock()
        product    = self.create_from_factory(ValidProductFactory, price=200)
        purchase   = self.create_from_factory(ValidPurchaseFactory, product=product)
        payment    = self.create_from_factory(ValidPaymentFactory, type='dummy', purchase=purchase, amount=200)
        transition = self.create_from_factory(ValidTransitionToPaidFactory, payment=payment)

        mockito.when(self.dummy).notify(purchase, payment, payload, 'notification').thenReturn(transition)
        mockito.when(self.mailer).notify_payment(purchase, payment)

        result = self.service.notify(purchase.id, payment.id, payload)

        self.assertEquals(result[0].status, 'paid')
        self.assertEquals(payment.status, 'paid')
        mockito.verify(self.mailer).notify_payment(purchase, payment)

    def test_notification_that_does_not_pay_the_balance_of_purchase(self):
        payload    = mockito.Mock()
        product    = self.create_from_factory(ValidProductFactory, price=200)
        purchase   = self.create_from_factory(ValidPurchaseFactory, product=product)
        payment    = self.create_from_factory(ValidPaymentFactory, type='dummy', purchase=purchase, amount=100)
        transition = self.create_from_factory(ValidTransitionToPaidFactory, payment=payment)

        mockito.when(self.dummy).notify(purchase, payment, payload, 'notification').thenReturn(transition)

        result = self.service.notify(purchase.id, payment.id, payload)

        self.assertEquals(payment.status, 'paid')
        self.assertEquals(result[0].status, 'pending')
        self.assertEquals(result[0].outstanding_amount, 100)
        mockito.verifyZeroInteractions(self.mailer)

    def test_notification_that_is_not_to_a_paid_state(self):
        payload    = mockito.Mock()
        product    = self.create_from_factory(ValidProductFactory, price=200)
        purchase   = self.create_from_factory(ValidPurchaseFactory, product=product)
        payment    = self.create_from_factory(ValidPaymentFactory, type='dummy', purchase=purchase, amount=100)
        transition = self.create_from_factory(ValidTransitionToPendingFactory, payment=payment)

        mockito.when(self.dummy).notify(purchase, payment, payload, 'notification').thenReturn(transition)

        result = self.service.notify(purchase.id, payment.id, payload)
        self.assertEquals(payment.status, 'pending')
        self.assertEquals(result[0].status, 'pending')
        self.assertEquals(result[0].outstanding_amount, 200)
        mockito.verifyZeroInteractions(self.mailer)

    def test_notifications_that_cannot_be_processed_throws_its_errors(self):
        payload    = mockito.Mock()
        product    = self.create_from_factory(ValidProductFactory, price=200)
        purchase   = self.create_from_factory(ValidPurchaseFactory, product=product)
        payment    = self.create_from_factory(ValidPaymentFactory, type='dummy', purchase=purchase, amount=100)
        transition = self.create_from_factory(ValidTransitionToPendingFactory, payment=payment)

        mockito.when(self.dummy).notify(purchase, payment, payload, 'notification').thenRaise(InvalidPaymentNotification)
        with self.assertRaises(InvalidPaymentNotification):
            self.service.notify(purchase.id, payment.id, payload)

        mockito.when(self.dummy).notify(purchase, payment, payload, 'notification').thenRaise(PaymentVerificationFailed)
        with self.assertRaises(PaymentVerificationFailed):
            self.service.notify(purchase.id, payment.id, payload)

        mockito.verifyZeroInteractions(self.mailer)

    def test_conclude_payment_of_already_valid_payment(self):
        payload = mockito.Mock()
        product    = self.create_from_factory(ValidProductFactory, price=200)
        purchase   = self.create_from_factory(ValidPurchaseFactory, product=product)
        payment    = self.create_from_factory(ValidPaymentFactory, type='dummy', purchase=purchase, amount=200)
        transition = self.create_from_factory(ValidTransitionToPendingFactory, payment=payment)
        mockito.when(self.dummy).conclude(payment, payload).thenReturn(transition)

        result = self.service.conclude(purchase.id, payment.id, payload)

        self.assertEquals(result, purchase)

    def test_conclude_payment_of_has_invalid_code(self):
        payload = mockito.Mock()
        product    = self.create_from_factory(ValidProductFactory, price=200)
        purchase   = self.create_from_factory(ValidPurchaseFactory, product=product)
        payment    = self.create_from_factory(ValidPaymentFactory, type='dummy', purchase=purchase, amount=200)
        transition = self.create_from_factory(ValidTransitionToPendingFactory, payment=payment)
        mockito.when(self.dummy).conclude(payment, payload).thenRaise(NoSuchPayment)

        with self.assertRaises(NoSuchPayment):
            self.service.conclude(purchase.id, payment.id, payload)

class PaymentFactoryTestCases(SegueApiTestCase):
    def setUp(self):
        super(PaymentFactoryTestCases, self).setUp()

    def test_payment_has_outstanding_amount_of_purchase_by_default(self):
        product  = self.create_from_factory(ValidProductFactory, price=200)
        purchase = self.create_from_factory(ValidPurchaseFactory, product=product)
        payment1 = self.create_from_factory(ValidPaymentFactory, purchase=purchase, amount=50)
        payment2 = self.create_from_factory(ValidPaymentFactory, purchase=purchase, amount=12.5, status='paid')
        payment3 = self.create_from_factory(ValidPaymentFactory, purchase=purchase, amount=12.5, status='confirmed')

        payment4 = PaymentFactory().create(purchase)

        self.assertEquals(payment4.amount, 175)
