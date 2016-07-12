from datetime import datetime
from segue.core import db
from sqlalchemy.sql import functions as func
from segue.errors import SegueError
from segue.product.models import Product
from segue.corporate.models import CorporatePurchase

PREFIXES = {
 'business':          'N',
 'corportate-promocode':  'N',
 'caravan':           'N',
 'caravan-leader':    'N',
 'sponsor':           'M',
 'foreigner':         'N',
 'foreigner-student': 'S',
 'government':        'E',
 'gov-promocode':     'E',
 'normal':            'N',
 'organization':      'O',
 'press':             'I',
 'promocode':         'N',
 'proponent':         'N',
 'proponent-student': 'S',
 'service':           'SE',
 'speaker':           'P',
 'student':           'S',
 'support':           'SU',
 'visitor':           'VVV',
 'volunteer':         'V'
}

CATEGORY_RECEPTION_DESK = {
 'business':          'pre',
 'corportate-promocode':  'pre',
 'caravan':           'pre',
 'caravan-leader':    'pre',
 'sponsor':           'pre',
 'foreigner':         'pre',
 'foreigner-student': 'pre',
 'government':        'pre',
 'gov-promocode':       'pre',
 'normal':            'pre',
 'organization':      'pre',
 'press':             'expopress',
 'promocode':         'pre',
 'proponent':         'pre',
 'proponent-student': 'pre',
 'service':           'expopress',
 'speaker':           'speaker',
 'student':           'pre',
 'support':           'expopress',
 'volunteer':         'pre',
}

class Badge(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    person_id    = db.Column(db.Integer, db.ForeignKey('purchase.id'))
    visitor_id   = db.Column(db.Integer, db.ForeignKey('visitor.id'))
    issuer_id    = db.Column(db.Integer, db.ForeignKey('account.id'))
    copies       = db.Column(db.Integer, default=1)
    printer      = db.Column(db.Text)
    name         = db.Column(db.Text)
    organization = db.Column(db.Text)
    city         = db.Column(db.Text)
    category     = db.Column(db.Text)
    job_id       = db.Column(db.Text)
    result       = db.Column(db.Text)
    prefix       = db.Column(db.Text)
    given        = db.Column(db.DateTime)

    created      = db.Column(db.DateTime, default=func.now())
    last_updated = db.Column(db.DateTime, onupdate=datetime.now)

    person  = db.relationship('Purchase', backref=db.backref('badges', lazy='dynamic'))
    visitor = db.relationship('Visitor',  backref=db.backref('badges', lazy='dynamic'))

    @classmethod
    def create(cls, target):
        badge = Badge()

        if isinstance(target, Visitor):
            badge.visitor = target
            badge.prefix  = PREFIXES.get('visitor',None)
        else:
            badge.person = target.purchase
            badge.prefix = PREFIXES.get(target.category,None)

        # we could've used a splat, but we want to control the arguments more finely
        data = target.badge_data
        for key in ['name','organization','city','category']:
            setattr(badge, key, data.get(key, None))

        return badge

    @property
    def xid(self):
        if self.person:    return self.person.id
        elif self.visitor: return self.visitor.id
        return 0

    @property
    def was_ok(self):
        return self.result != 'failed'

    def print_data(self):
        return dict(
            prefix       = self.prefix,
            xid          = self.xid,
            name         = self.name,
            city         = self.city,
            organization = self.organization,
            category     = self.category,
            copies       = self.copies
        )

class Visitor(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.Text)
    email    = db.Column(db.Text)
    document = db.Column(db.Text)
    phone    = db.Column(db.Text)
    badge_name = db.Column(db.Text)

    created      = db.Column(db.DateTime, default=func.now())
    last_updated = db.Column(db.DateTime, onupdate=datetime.now)

    #TODO CHECK
    @property
    def badge_data(self):
        return dict(
            name         = self.name,
            city         = None,
            category     = "visitor",
            organization = "visitante"
        )

    @property
    def can_print_badge(self):
        return True


class Person(object):
    def __init__(self, purchase, links=False):
        self.id           = purchase.id

        self.customer_id   = purchase.customer.id
        self.role         = purchase.customer.role
        self.name         = purchase.customer.name
        self.email        = purchase.customer.email
        self.document     = purchase.customer.document
        self.phone        = purchase.customer.phone
        self.organization = purchase.customer.organization
        self.badge_name   = purchase.badge_name
        self.badge_corp   = purchase.badge_corp

        self.city                 = purchase.customer.city
        self.country              = purchase.customer.country
        self.address_state        = purchase.customer.address_state
        self.address_neighborhood = purchase.customer.address_neighborhood
        self.address_street       = purchase.customer.address_street
        self.address_number       = purchase.customer.address_number
        self.address_extra        = purchase.customer.address_extra
        self.address_zipcode      = purchase.customer.address_zipcode

        self.has_promocode   = purchase.customer.has_promocode

        self.product_description = purchase.product.description
        self.category            = purchase.product.category
        self.price               = purchase.product.price
        self.buyer               = purchase.buyer
        self.purchase            = purchase

    @property
    def reception_desk(self):
        if not self.is_valid_ticket: return 'new'
        return CATEGORY_RECEPTION_DESK.get(self.category, 'pre')


    @property
    def has_payable_ticket(self):
        return self.purchase.payable

    @property
    def donation_promocodes(self):
        from segue.models import PromoCode

        donation_products = db.session.query(Product.promocode_product_id).filter(Product.category == 'donation').subquery()
        return PromoCode.query\
                 .filter(PromoCode.creator_id == self.customer_id)\
                 .filter(PromoCode.product_id.in_(donation_products)).all()

    @property
    def related_people(self):
        all_purchases = self.purchase.customer.purchases[:]
        other_purchases = [ x for x in all_purchases if x.id != self.id ]
        return map(Person, other_purchases)

    @property
    def product(self):
        return self.purchase.product

    @property
    def kind(self):
        return self.purchase.product.kind

    @property
    def outstanding_amount(self):
        if self.is_valid_ticket: return None
        return self.purchase.outstanding_amount

    @property
    def related_count(self):
        return len(self.purchase.customer.purchases) - 1

    @property
    def is_brazilian(self):
        return self.purchase.customer.is_brazilian

    @property
    def is_corporate(self):
        print(self.category)
        if self.category == 'business' or self.category == 'government':  return True
        else: return False

    @property
    def is_valid_ticket(self):
        if self.category == 'donation': return False
        if self.category == 'government' and self.status == 'pending': return True
        return self.status == 'paid'


    @property
    def status(self):
        if self.category == 'government' and self.purchase.status == 'pending': return 'paid'
        else: return self.purchase.status

    @property
    def can_print_badge(self):
        return self.is_valid_ticket

    @property
    def can_change_badge_corp(self):
        return True

    @property
    def last_badge(self):
        return self.purchase.badges.order_by(Badge.created.desc()).first()

    @property
    def badge_data(self):
        return dict(
            city         = self.city,
            category     = self.category,
            name         = self.badge_name,
            organization = self.badge_corp
        )

    @property
    def is_stale(self):
        return self.status == 'stale'

    @property
    def can_change_product(self):
        return not (self.purchase.stale or self.purchase.satisfied or self.purchase.has_started_payment)

    @property
    def eligible_donation_products(self):
        products = []

        for product in Product.query.filter(Product.category=='donation').order_by(Product.price).all():
            try:
                if not product.can_pay_cash and product.sold_until > datetime.now():
                    continue
                elif product.check_eligibility({}, self.purchase.customer):
                    products.append(product)
            except SegueError, e:
                pass

        return products

    @property
    def eligible_products(self):
        if self.is_valid_ticket: return []
        if not self.can_change_product: return []
        products = []

        for product in Product.query.all():
            try:
                if not product.can_pay_cash:
                    continue
                elif product.check_eligibility({}, self.purchase.customer):
                    products.append(product)
            except SegueError, e:
                pass

        cheapest = {}
        for product in products:
            if not cheapest.get(product.category, None):
                cheapest[product.category] = product
            elif cheapest[product.category].price > product.price:
                cheapest[product.category] = product

        return sorted(cheapest.values(), key=lambda p: p.price)
