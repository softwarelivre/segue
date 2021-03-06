from decimal import Decimal
from datetime import datetime, timedelta

import mockito

from segue.purchase.promocode import PromoCodeService

from ..support import SegueApiTestCase, hashie
from ..support.factories import *
from click.testing import Result

class PromoCodeServiceTestCase(SegueApiTestCase):
    def setUp(self):
        super(PromoCodeServiceTestCase, self).setUp()
        self.mock_hasher = mockito.mock()
        self.service = PromoCodeService(hasher=self.mock_hasher)

    def test_calculates_paid_amount(self):
        product_price = 100
        promo = self.create(ValidPromoCodeFactory, hash_code="DEFG5678", discount=0.2)

        product = self.create(ValidProductFactory, price=product_price)
        purchase = self.create(ValidPurchaseFactory, product=product, amount=product_price)
        payment = self.create(ValidPromoCodePaymentFactory, purchase=purchase, promocode=promo)

        self.assertEqual(payment.paid_amount, 20)
        self.assertEqual(purchase.outstanding_amount, 80)

    def test_query(self):
        payment = self.create(ValidPromoCodePaymentFactory)
        pc1 = self.create(ValidPromoCodeFactory, hash_code="ABCD1234", description="amigo do rei")
        pc2 = self.create(ValidPromoCodeFactory, hash_code="DEFG5678", payment=payment)

        result = self.service.query(hash_code="ABCD")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], pc1)

        result = self.service.query(used=True)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], pc2)

        result = self.service.query(description="amigo")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], pc1)

    def test_lookup(self):
        payment = self.create(ValidPromoCodePaymentFactory)
        pc1 = self.create(ValidPromoCodeFactory, hash_code="ABCD1234", description="amigo do rei")
        pc2 = self.create(ValidPromoCodeFactory, hash_code="DEFG5678", payment=payment)

        pagination = self.service.lookup(criteria=dict(hash_code="ABCD"))
        self.assertEqual(pagination.total, 1)
        self.assertEqual(pagination.items[0], pc1)

        result = self.service.lookup(criteria=dict(hash_code="amigo"))
        self.assertEqual(pagination.total, 1)
        self.assertEqual(pagination.items[0], pc1)

    def test_must_not_return_a_promocode_out_of_the_valid_date(self):
        start_at = date.today() - timedelta(days=7)
        end_at = date.today() - timedelta(days=5)
        
        pc = self.create(ValidPromoCodeFactory, start_at=start_at, end_at=end_at)
        
        result = self.service.check(pc.hash_code)
        self.assertIsNone(result)
    
    def test_must_return_a_promocode_valid_per_one_day(self):
        start_at = date.today()
        end_at = date.today()
        
        pc = self.create(ValidPromoCodeFactory, start_at=start_at, end_at=end_at)
        
        result = self.service.check(pc.hash_code)
        self.assertIsNotNone(result)


    def test_check(self):
        payment = self.create(ValidPromoCodePaymentFactory)

        pc1 = self.create(ValidPromoCodeFactory)
        pc2 = self.create(ValidPromoCodeFactory, payment=payment)

        result = self.service.check(pc1.hash_code)
        self.assertEqual(result, pc1)

        result = self.service.check(pc2.hash_code)
        self.assertEqual(result, None)

        result = self.service.check("blabla")
        self.assertEqual(result, None)

    def test_creation(self):
        product = self.create(ValidProductFactory)
        creator = self.create(ValidAccountFactory)
        #TODO: IMPROVE
        start_at = datetime.today() + timedelta(days=7)
        end_at = datetime.today() - timedelta(days=7)
        promocode = {
            'product_id': product.id,  
            'description': 'empresa x', 
            'start_at': datetime.strftime(start_at, "%d/%m/%Y"),
            'end_at': datetime.strftime(start_at, "%d/%m/%Y"), 
            'discount': 0.7     
        }
    
        mockito.when(self.mock_hasher).generate().thenReturn('A').thenReturn('B').thenReturn('C')

        result = self.service.create(promocode, creator=creator, quantity=3)

        self.assertEqual(len(result), 3)

        discounts = [ x.discount for x in result ]
        self.assertEqual(set(discounts), set([ Decimal('0.7') ]))

        products = [ x.product for x in result ]
        self.assertEqual(set(products), set([product]))

        creators = [ x.creator for x in result ]
        self.assertEqual(set(creators), set([creator]))

        hashes = [ x.hash_code for x in result ]
        self.assertEqual(hashes, ['A','B','C'])

        descriptions = [ x.description for x in result ]
        self.assertEqual(descriptions[0], 'empresa x - 1/3')
        self.assertEqual(descriptions[1], 'empresa x - 2/3')
        self.assertEqual(descriptions[2], 'empresa x - 3/3')

