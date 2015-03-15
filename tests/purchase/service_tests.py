import mockito

from segue.purchase.services import PurchaseService, PaymentService
from segue.purchase.models import Payment, PagSeguroPayment
from segue.errors import NotAuthorized

from ..support import SegueApiTestCase
from ..support.factories import *


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

    def test_retrieving_a_purchase(self):
        other_account = self.create_from_factory(ValidAccountFactory)
        purchase      = self.create_from_factory(ValidPurchaseFactory)

        result = self.service.get_one(purchase.id, by=purchase.customer)
        self.assertEquals(result.id, purchase.id)

        with self.assertRaises(NotAuthorized):
            self.service.get_one(purchase.id, by=other_account)

class PaymentServiceTestCases(SegueApiTestCase):
    def setUp(self):
        super(PaymentServiceTestCases, self).setUp()
        self.dummy = mockito.Mock()
        self.service = PaymentService(dummy=self.dummy)

    def test_creating_a_payment_delegates_creation_and_processing_to_correct_payment_implementation(self):
        data = dict(got='mock?')
        instructions = dict(got='result?')
        purchase = self.create_from_factory(ValidPurchaseFactory)
        payment = self.build_from_factory(ValidPaymentFactory)

        mockito.when(self.dummy).create(purchase, data).thenReturn(payment)
        mockito.when(self.dummy).process(payment).thenReturn(instructions)

        result = self.service.create(purchase, 'dummy', data)

        self.assertEquals(result, instructions)

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
