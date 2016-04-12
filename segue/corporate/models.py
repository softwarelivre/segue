import datetime
from sqlalchemy.sql import functions as func
from ..core import db
from ..json import JsonSerializable
from segue.purchase.models import Purchase, Payment, Transition
from segue.account.models import Account
from segue.product.errors import WrongBuyerForProduct
from errors import InvalidPurchaseQuantity

from serializers import *

class Corporate(JsonSerializable, db.Model):
    _serializers     = [ CorporateJsonSerializer ]
    id               = db.Column(db.Integer, primary_key=True)
    owner_id         = db.Column(db.Integer, db.ForeignKey('account.id'))
    kind             = db.Column(db.Text, server_default='corporate')

    name             = db.Column(db.Text)
    badge_name       = db.Column(db.Text)
    document         = db.Column(db.Text)
    address_street   = db.Column(db.Text)
    address_number   = db.Column(db.Text)
    address_extra    = db.Column(db.Text)
    address_district = db.Column(db.Text)
    address_city     = db.Column(db.Text)
    address_state    = db.Column(db.Text)
    address_zipcode  = db.Column(db.Text)
    incharge_name    = db.Column(db.Text)
    incharge_email   = db.Column(db.Text)
    incharge_phone_1 = db.Column(db.Text)
    incharge_phone_2 = db.Column(db.Text)

    created          = db.Column(db.DateTime, default=func.now())
    last_updated     = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    owner = db.relationship('Account', back_populates='corporate_owned', foreign_keys=[owner_id], uselist=False)

    purchases        = db.relationship('CorporatePurchase' , backref=db.backref('corporate', uselist=False))

    __mapper_args__ = { 'polymorphic_on': kind, 'polymorphic_identity': 'business' }

EmployeeAccount = Account



class CorporatePurchase(Purchase):
    __mapper_args__ = { 'polymorphic_identity': 'corporate' }
    corporate_id = db.Column(db.Integer, db.ForeignKey('corporate.id'), name='cr_corporate_id')

    def __init__(self, **extra_fields):
        Purchase.__init__(self, **extra_fields)
        qty = extra_fields.get('qty', 0)
        if qty <= 0:
            raise InvalidPurchaseQuantity()
        else:
            self.qty = qty

    @property
    def badge_corp(self):
        if not self.corporate: return ''
        return self.corporate.badge_name

    @property
    def can_change_badge_corp(self):
        return False


class EmployeePurchase(CorporatePurchase):
    __mapper_args__ = { 'polymorphic_identity': 'employee' }

class DepositPayment(Payment):
    __mapper_args__ = { 'polymorphic_identity': 'deposit' }

    @property
    def extra_fields(self):
        return dict(description=self.description)

class DepositTransition(Transition):
    __mapper_args__ = { 'polymorphic_identity': 'deposit' }


class GovCorporate(Corporate):
    __mapper_args__ = { 'polymorphic_identity': 'government' }


class GovPurchase(CorporatePurchase):
    __mapper_args__ = {'polymorphic_identity': 'government'}

    def __init__(self, **extra_fields):
        CorporatePurchase.__init__(self, **extra_fields)
        #TODO: FIX REMOVE QTY CHECK
        qty = extra_fields.get('qty', 0)
        if qty <= 0:
            raise InvalidPurchaseQuantity()
        else:
            self.qty = qty

        self.status = 'gov_document_submission_pending'


class GovPayment(Payment):
    __mapper_args__ = { 'polymorphic_identity': 'government' }

    @property
    def extra_fields(self):
        result = dict(description=self.description)
        if hasattr(self.purchase, 'corporate'):
            result['payer_name'] = self.purchase.corporate.name
        return result



class GovTransition(Transition):
    __mapper_args__ = { 'polymorphic_identity': 'government' }
