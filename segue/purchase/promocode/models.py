# -*- coding: utf-8 -*-

from segue.core import db
from ..models import Payment, Transition
from segue.json import JsonSerializable

class PromoCode(JsonSerializable, db.Model):
    __tablename__ = 'promocode'

    id             = db.Column(db.Integer, primary_key=True)
#    kind           = db.Column(db.Text,    server_default='normal')
    creator_id     = db.Column(db.Integer, db.ForeignKey('account.id'))
    product_id     = db.Column(db.Integer, db.ForeignKey('product.id'))
    hash_code      = db.Column(db.String(32))
    description    = db.Column(db.Text)
    discount       = db.Column(db.Numeric)

    start_at   = db.Column(db.Date)
    end_at     = db.Column(db.Date)

    creator = db.relationship('Account')
    product = db.relationship('Product', backref='promocodes')
    payment = db.relationship('PromoCodePayment', uselist=False, backref=db.backref('promocode', uselist=False))

#    __mapper_args__ = { 'polymorphic_on': kind, 'polymorphic_identity': 'normal' }

    @property
    def used(self):
        return self.payment is not None

    @property
    def used_by(self):
        if self.used:
            return self.payment.purchase.customer

class PromoCodePayment(Payment):
    __mapper_args__ = { 'polymorphic_identity': 'promocode' }

    promocode_id     = db.Column(db.Integer, db.ForeignKey('promocode.id'), name='pc_promocode_id')

    @property
    def extra_fields(self):
        if not self.promocode: return {}
        return dict(hash_code=self.promocode.hash_code, discount=self.promocode.discount)

    @property
    def paid_amount(self):
        valid = self.promocode != None
        total_value = self.purchase.total_amount
        if valid:
            discounted  = self.promocode.discount * total_value
        return discounted if valid else 0

class PromoCodeTransition(Transition):
    __mapper_args__ = { 'polymorphic_identity': 'promocode' }
