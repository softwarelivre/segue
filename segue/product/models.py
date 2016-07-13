from datetime import datetime
from sqlalchemy import func
from ..json import JsonSerializable, SQLAlchemyJsonSerializer
from ..core import db

from errors import ProductExpired, MinimumAmount, MaxPurchaseReached, AlreadyUsed
from segue.corporate.models import CorporatePurchase, GovPurchase
from segue.purchase.promocode.models import PromoCode
from segue.purchase.models import Purchase, StudentPurchase, DonationPurchase

class ProductJsonSerializer(SQLAlchemyJsonSerializer):
    _serializer_name = 'normal'

class Product(JsonSerializable, db.Model):
    _serializers      = [ ProductJsonSerializer ]
    id                = db.Column(db.Integer, primary_key=True)
    kind              = db.Column(db.Enum('worker', 'public', 'speaker', name="product_kinds"))
    category          = db.Column(db.Text)
    public            = db.Column(db.Boolean, default=True)
    max_purchases     = db.Column(db.Integer, default=0)
    price             = db.Column(db.Numeric)
    due_date          = db.Column(db.Date)
    sold_until        = db.Column(db.DateTime)
    description       = db.Column(db.Text)
    information       = db.Column(db.Text)
    is_promo          = db.Column(db.Boolean, default=False, server_default='f')
    is_speaker        = db.Column(db.Boolean, default=False, server_default='f')
    gives_kit         = db.Column(db.Boolean, default=True,  server_default='t')
    can_pay_cash      = db.Column(db.Boolean, default=False, server_default='f')
    original_deadline = db.Column(db.DateTime)
    promocode_product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

    purchases  = db.relationship("Purchase", backref="product")

    __tablename__ = 'product'
    __mapper_args__ = { 'polymorphic_on': category, 'polymorphic_identity': 'normal' }

    def __repr__(self):
        return "<Product({})={}>".format(self.category, self.price)

    @property
    def gives_promocode(self):
        if self.promocode_product_id:
            return True
        else:
            return False

    def check_eligibility(self, buyer_data, account=None):
        if self.sold_until < datetime.now():
            raise ProductExpired()
        if self.is_limited() and self.purchase_limit_reachead():
            raise MaxPurchaseReached()
        return True

    def extra_purchase_fields_for(self, buyer_data):
        return {}

    def special_purchase_class(self):
        return None

    def is_limited(self):
        return self.max_purchases > 0

    def purchase_limit_reachead(self):
        count = db.session.query(func.count(Purchase.id))\
            .filter(Purchase.product_id == self.id)\
            .scalar()
        if not count:
            return False
        if count >= self.max_purchases:
            return True
        else:
            return False

    def similar_products(self):
        return Product.query.filter(
                Product.category   == self.category,
                Product.kind       == self.kind,
                Product.sold_until >  datetime.now())

class LockedProduct(Product):
    def check_eligibility(self):
        return False

class PressProduct(LockedProduct):
    __mapper_args__ = { 'polymorphic_identity': 'press' }

class SupportProduct(LockedProduct):
    __mapper_args__ = { 'polymorphic_identity': 'support' }

class ServiceProduct(LockedProduct):
    __mapper_args__ = { 'polymorphic_identity': 'service' }

class ExhibitorProduct(LockedProduct):
    __mapper_args__ = { 'polymorphic_identity': 'exhibitor' }

class OrganizationProduct(LockedProduct):
    __mapper_args__ = { 'polymorphic_identity': 'organization' }

class SponsorProduct(LockedProduct):
    __mapper_args__ = { 'polymorphic_identity': 'sponsor' }

    def check_eligibility(self, buyer_data, account=None):
        return True

class VolunteerProduct(LockedProduct):
    __mapper_args__ = { 'polymorphic_identity': 'volunteer' }

class PromoCodeProduct(Product):
    __mapper_args__ = { 'polymorphic_identity': 'promocode' }

    def check_eligibility(self, buyer_data, account=None):
        hash_code = buyer_data.get('hash_code',None)
        if not hash_code: return False

        promocodes = PromoCode.query.filter(PromoCode.hash_code == hash_code).all()
        if not promocodes: return False

        #TODO CREATE A DATABASE CONTRAINT
        for promocode in promocodes:
            if promocode.product != self:
                return False

        # ONE PRODUCT PER CLIENT FOR PROMOCODES WITH SAME HASH
        if db.session.query(func.count(Purchase.id)) \
            .filter(Purchase.product_id == promocode.product.id) \
            .filter(Purchase.customer_id == account.id).scalar():
            raise AlreadyUsed()

        return True


class CorporatePromoCodeProduct(PromoCodeProduct):
    __mapper_args__ = {'polymorphic_identity': 'corporate-discount-promocode'}

    def special_purchase_class(self):
        return CorporatePurchase

    def check_eligibility(self, buyer_data, account=None):
        hash_code = buyer_data.get('hash_code', None)
        if not account or not account.is_corporate:
            return False

        promocodes = PromoCode.query.filter(PromoCode.hash_code == hash_code).all()
        if not promocodes: return False

        for promocode in promocodes:
            if promocode.product != self:
                return False

        # ONE PRODUCT PER CLIENT FOR PROMOCODES WITH SAME HASH
        if db.session.query(func.count(Purchase.id)) \
                .filter(Purchase.product_id == promocode.product.id) \
                .filter(Purchase.customer_id == account.id).scalar():
            raise AlreadyUsed()

        return True



    def extra_purchase_fields_for(self, buyer_data):
        import decimal
        qty = buyer_data.get('purchase_qty', 0)
        return {'qty': decimal.Decimal(qty)}


class CorporatePromoCode(PromoCodeProduct):
    __mapper_args__ = {'polymorphic_identity': 'corporate-promocode'}

class GovPromoCode(PromoCodeProduct):
    __mapper_args__ = {'polymorphic_identity': 'gov-promocode'}


class StudentProduct(Product):
    __mapper_args__ = { 'polymorphic_identity': 'student' }

    def special_purchase_class(self):
        return StudentPurchase

class ForeignerProduct(Product):
    __mapper_args__ = { 'polymorphic_identity': 'foreigner' }

    def check_eligibility(self, buyer_data, account=None):
        if not account: return False
        return not account.is_brazilian

class ForeignerStudentProduct(ForeignerProduct):
    __mapper_args__ = { 'polymorphic_identity': 'foreigner-student' }

class CorporateProduct(Product):
    __mapper_args__ = { 'polymorphic_identity': 'business' }

    def special_purchase_class(self):
        return CorporatePurchase

    def check_eligibility(self, buyer_data, account=None):
        if not account: return False
        return account.is_corporate

    def extra_purchase_fields_for(self, buyer_data):
        qty = buyer_data.get('purchase_qty', 0)
        return {'qty': qty}


class GovernmentProduct(Product):
    __mapper_args__ = { 'polymorphic_identity': 'government' }

    def special_purchase_class(self):
        return GovPurchase

    def check_eligibility(self, buyer_data, account=None):
        if not account: return False
        return account.is_government

    def extra_purchase_fields_for(self, buyer_data):
        qty = buyer_data.get('purchase_qty', 0)
        return {'qty': qty}

class DonationProduct(Product):
    __mapper_args__ = {'polymorphic_identity': 'donation'}

    def special_purchase_class(self):
        return DonationPurchase

    def extra_purchase_fields_for(self, buyer_data):
        """ Used in service.purchase for get the data from the request and send to the model"""
        give_tshirt = [1,13,58,71,73]

        #TODO: REVIEW HARDCODING
        extra_fields = {}

        if self.id in give_tshirt:
            extra_fields['shirt_size'] = buyer_data.get('shirt_size', None)
            extra_fields['delivery'] = buyer_data.get('delivery', None)

        #A donation without a fixed price
        if not self.price:
            if 'amount' in buyer_data:
                amount = float(buyer_data['amount'])
                if amount < 10:
                    raise MinimumAmount()
                extra_fields['amount'] = buyer_data['amount']

        return extra_fields