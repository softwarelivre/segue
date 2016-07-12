# -*- coding: utf-8 -*-

from datetime import datetime

from sqlalchemy.sql import functions as func
from ..json import JsonSerializable, SQLAlchemyJsonSerializer
from ..core import db

from serializers import *

import re

class Buyer(JsonSerializable, db.Model):
    _serializers = [ BuyerJsonSerializer ]
    id              = db.Column(db.Integer, primary_key=True)
    kind            = db.Column(db.Enum('person','company','government', name="buyer_kinds"))
    name            = db.Column(db.Text)
    document        = db.Column(db.Text)
    extra_document  = db.Column(db.String(length=80))
    document_file_hash = db.Column(db.String(length=80))
    contact         = db.Column(db.Text)
    address_street  = db.Column(db.Text)
    address_number  = db.Column(db.Text)
    address_extra   = db.Column(db.Text)
    address_zipcode = db.Column(db.Text)
    address_city    = db.Column(db.Text)
    address_country = db.Column(db.Text)
    address_state   = db.Column(db.Text)
    address_neighborhood = db.Column(db.Text)
    purchases       = db.relationship('Purchase', backref='buyer')

    @property
    def address_fields(self):
        result = {}
        for field in self.__mapper__.iterate_properties:
            if field.key.startswith('address_'):
                name = field.key.split("_")[-1]
                result[name] = getattr(self, field.key) or ''
        return result


    def is_brazilian(self): #FIX ME
        if self.address_country.upper() == 'BR':
            return True
        return re.match(r"bra.*", self.address_country or '', re.IGNORECASE) != None

    @property
    def complete_address(self):
        return u"{street} {number} {extra} - {city} {country}".format(**self.address_fields)

class Purchase(JsonSerializable, db.Model):
    _serializers = [ PurchaseJsonSerializer, ShortPurchaseJsonSerializer ]

    id             = db.Column(db.Integer, primary_key=True)
    product_id     = db.Column(db.Integer, db.ForeignKey('product.id'))
    customer_id    = db.Column(db.Integer, db.ForeignKey('account.id'))
    buyer_id       = db.Column(db.Integer, db.ForeignKey('buyer.id'))
    qty            = db.Column(db.Integer, default=1)
    #TODO: Create a enum for status. Status from database an old database ( pending, paid, reimbursed, stale)
    status         = db.Column(db.Text, default='pending')
    amount         = db.Column(db.Numeric)
    due_date       = db.Column(db.Date)
    created        = db.Column(db.DateTime, default=func.now())
    last_updated   = db.Column(db.DateTime, onupdate=datetime.now)
    kind           = db.Column(db.Text, server_default='single')
    hash_code      = db.Column(db.String(64))

    payments       = db.relationship('Payment', backref='purchase', lazy='dynamic')

    __tablename__ = 'purchase'
    __mapper_args__ = { 'polymorphic_on': kind, 'polymorphic_identity': 'single' }

    def __repr__(self):
        return "<[{}][{}]:{}-{}>".format(self.id, self.category, self.customer.email, self.status)

    @property
    def category(self):
        return self.product.category

    @property
    def badge_name(self):
        if not self.customer: return ''
        return self.customer.badge_name or self._make_badge_name(self.customer.name) or ''

    def _make_badge_name(self, customer_name):
        if not customer_name: return ''
        if len(customer_name) <= 20: return customer_name
        splited_name = customer_name.split(' ')
        if len(splited_name) > 1:
            badge_name = splited_name[0] + ' ' + splited_name[-1]
            if len(badge_name) <= 20:
                return badge_name
        return ''

    @property
    def badge_corp(self):
        if not self.customer: return ''
        return self.customer.organization

    @property
    def can_change_badge_corp(self):
        return True

    @property
    def valid_payments(self):
        return self.payments.filter(Payment.status.in_(Payment.VALID_PAYMENT_STATUSES))

    @property
    def payable(self):
        #TODO: FIX THERE ARE PURCHASES WITHOUT DUE_DATE
        expired = True
        if self.due_date:
            expired = self.due_date <= datetime.now().date()
            print(self.due_date, datetime.now().date(), expired)
        return not self.status in ['stale', 'reimbursed', 'cancelled','paid'] and not expired

    @property
    def stale(self):
        return self.status == 'stale'

    @property
    def reimbursed(self):
        return self.status == 'reimbursed'

    @property
    def could_be_stale(self):
        return not self.reimbursed and not self.stale and not self.satisfied and datetime.now().date() > self.due_date

    @property
    def paid_amount(self):
        for p in self.payments:
            print type(p)

        return sum([ p.paid_amount for p in self.payments])

    @property
    def total_amount(self):
        return self.amount * self.qty

    @property
    def outstanding_amount(self):
        return self.total_amount - self.paid_amount

    @property
    def has_started_payment(self):
        return self.outstanding_amount < self.amount

    @property
    def satisfied(self):
        return self.status == 'paid' or self.status == 'confirmed'

    def payment_analysed(self):
        if self.status == 'payment_analysis':
            self.status = 'paid'

    @property
    def description(self):
        return self.product.description

    @property
    def can_start_payment(self):
        return self.due_date >= datetime.now().date()

    def had_paid_with_cash(self):
        for payment in self.payments:
            if payment.type == 'cash':
                return True

    def recalculate_status(self):
        self.status = 'paid' if self.outstanding_amount == 0 else 'pending'

    def clone(self):
        arguments = dict()
        for name, column in self.__mapper__.columns.items():
            if name == 'created': continue
            if not (column.primary_key or column.unique):
                arguments[name] = getattr(self, name)
        return self.__class__(**arguments)


class StudentPurchase(Purchase):
    __mapper_args__ = {'polymorphic_identity': 'student'}

    def recalculate_status(self):
        if self.outstanding_amount == 0:
            if self.buyer.extra_document or self.had_paid_with_cash():
                self.status = 'paid'
            else:
                self.status = 'student_document_in_analysis'

    def payment_analysed(self):
        if self.status == 'student_document_in_analysis':
            self.status = 'paid'
        return self.status

class DonationPurchase(Purchase):
    #TODO: IMPROVE THIS CLASS
    __mapper_args__ = {'polymorphic_identity': 'donation'}

    def __init__(self, *args, **kwargs):
        Purchase.__init__(self, *args, **kwargs)
        self.amount = kwargs.pop('amount', 0)

class ExemptPurchase(Purchase):
    __mapper_args__ = { 'polymorphic_identity': 'exempt' }

class PaymentJsonSerializer(SQLAlchemyJsonSerializer):
    _serializer_name = 'normal'

class Payment(JsonSerializable, db.Model):
    VALID_PAYMENT_STATUSES = ['paid','confirmed']

    _serializers = [ PaymentJsonSerializer ]
    id          = db.Column(db.Integer, primary_key=True)
    type        = db.Column(db.String(20))
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'))
    status      = db.Column(db.Text, default='pending')
    amount      = db.Column(db.Numeric)
    due_date    = db.Column(db.Date)
    description = db.Column(db.Text)

    transitions = db.relationship('Transition', backref='payment', lazy='dynamic')

    __tablename__ = 'payment'
    __mapper_args__ = { 'polymorphic_on': type, 'polymorphic_identity': 'payment' }

    @property
    def extra_fields(self):
        return {}

    @property
    def paid_amount(self):
        valid = self.status in Payment.VALID_PAYMENT_STATUSES
        return self.amount if valid else 0

    @property
    def most_recent_transition(self):
        return self.transitions.order_by(Transition.created.desc()).first()

    def recalculate_status(self):
        self.status = self.most_recent_transition.new_status

class Transition(JsonSerializable, db.Model):
    _serializers   = [ TransitionJsonSerializer ]
    id             = db.Column(db.Integer, primary_key=True)
    type           = db.Column(db.String(20))
    payment_id     = db.Column(db.Integer, db.ForeignKey('payment.id'))
    old_status     = db.Column(db.Text)
    new_status     = db.Column(db.Text)
    source         = db.Column(db.Text)
    created        = db.Column(db.DateTime, default=func.now())

    __tablename__ = 'transition'
    __mapper_args__ = { 'polymorphic_on': type, 'polymorphic_identity': 'transition' }

    @property
    def is_payment(self):
        return self.old_status != 'paid' and self.new_status == 'paid'


class ClaimCheck(object):

    def __init__(self, purchase, date=None, hash_code=None):
        self.purchase = purchase
        self.date = date or datetime.now()
        self.hash_code = hash_code

    @property
    def template_vars(self):
        # CAST INT AND YEAR TO STR TO AVOID PROBLEMS WITH METHOD ESCAPE FROM svg_to_pdf
        return {'PURCHASE_ID': str(self.purchase.id),
                'NAME': self.purchase.customer.name,
                'DOCUMENT': self.purchase.customer.document,
                'AMOUNT': '{:.02f}'.format(float(self.purchase.amount)),
                'DAY': '{:02d}'.format(self.date.day),
                'MONTH': '{:02d}'.format(self.date.month),
                'YEAR': str(self.date.year)}

    @property
    def template_file(self):
        return 'purchase/templates/donationclaimcheck.svg'
