import jsonschema
from datetime import datetime
from redis import Redis
from rq import Queue

from segue.core import db, config, logger
from segue.filters import FilterStrategies
from segue.errors import SegueValidationError, SchemaValidationError
from segue.hasher import Hasher
from segue.mailer import MailerService

from segue.models import Purchase
from segue.account.services import AccountService
from segue.purchase.services import PurchaseService, PaymentService
from segue.purchase.errors import PurchaseAlreadySatisfied
from segue.purchase.cash import CashPaymentService
from segue.purchase.promocode import PromoCodePaymentService
from segue.purchase.factories import BuyerFactory
from segue.product.errors import WrongBuyerForProduct
from segue.product.services import ProductService

from errors import TicketIsNotValid, MustSpecifyPrinter, CannotPrintBadge, InvalidPrinter, InvalidPaymentOperation, CannotChangeProduct
from models import Person, Badge, Visitor
from filters import FrontDeskFilterStrategies
import schema

def _validate(schema_name, data):
    validator = jsonschema.Draft4Validator(schema.whitelist.get(schema_name), format_checker=jsonschema.FormatChecker())
    errors = list(validator.iter_errors(data))
    if errors:
        logger.error('validation error for person patch: %s', errors)
        raise SegueValidationError(errors)

class PrinterService(object):
    def __init__(self, name='default', queue_host=None, queue_password=None):
        host     = queue_host     or config.QUEUE_HOST
        password = queue_password or config.QUEUE_PASSWORD
        redis_conn = Redis(host=host, password=password)
        self.queue = Queue(name, connection=redis_conn)

    def print_badge(self, badge):
        return self.queue.enqueue('worker.print_badge', badge.print_data())

class BadgeService(object):
    def __init__(self, override_config=None):
        self.config = override_config or config
        self.printers = { name: PrinterService(name) for name in config.PRINTERS }

    def latest_attempt_for_person(self, person_id):
        return Badge.query.filter(Badge.person_id == person_id).order_by(Badge.created.desc()).first()

    def was_ever_printed(self, person_id):
        return self.latest_attempt_for_person(person_id) != None

    def has_failed_recently(self, person_id):
        latest_attempt = self.latest_attempt_for_person(person_id)
        if not latest_attempt: return False
        return latest_attempt.result == 'failed'

    def mark_failed_for_person(self, person_id):
        lattest_attempt = self.latest_attempt_for_person(person_id)
        if not latest_attempt: return False
        latest_attempt.result = 'failed'
        db.session.add(latest_attempt)
        db.session.commit()
        return True

    def report_failure(self, job_id):
        badge = Badge.query.filter(Badge.job_id == job_id).first()
        if not badge: return False
        if badge.result == 'failed': return False
        badge.result = 'failed'
        db.session.add(badge)
        db.session.commit()
        return True

    def report_success(self, job_id):
        badge = Badge.query.filter(Badge.job_id == job_id).first()
        if not badge: return False
        if badge.result == 'success': return False
        badge.result = 'success'
        db.session.add(badge)
        db.session.commit()
        return True

    def make_badge(self, printer, visitor_or_person, organization=None, copies=1, by_user=None):
        #if not visitor_or_person.can_print_badge: raise CannotPrintBadge()
        if printer not in self.printers: raise InvalidPrinter()
        badge = Badge.create(visitor_or_person)
        badge.printer = printer
        badge.issuer  = by_user
        badge.copies  = copies
        if organization: badge.organization = organization
        badge.job_id  = self.printers[printer].print_badge(badge).id
        db.session.add(badge)
        db.session.commit()

    def give_badge(self, badge_id):
        badge = Badge.query.filter(Badge.id == badge_id).first()
        if not badge: return None
        badge.given = datetime.now()
        db.session.add(badge)
        db.session.commit()
        return badge


class SpeakerService(object):
    def __init__(self, purchases=None, accounts=None, badges=None):
        self.badges = badges or BadgeService()
        self.purchases = purchases or PurchaseService()
        self.accounts = accounts or AccountService()
        self.products = ProductService()
        self.peoples = PeopleService()

    def create(self, ticket=None, printer=None, by_user=None, **data):
        #TODO: FIX
        product = self.products.chepest_available_for(ticket)
        account = self.accounts.create_people(data)
        purchase = self.purchases.give_ticket(account, product, commit=False)
        db.session.add(account)
        db.session.add(purchase)
        db.session.commit()

        logger.info('SpeakerService.create  email={} type={} by={}'.format(account.email,product.category,by_user))

        people = self.peoples.get_one(purchase.id, by_user=None, check_ownership=False, strict=True)
        self.badges.make_badge(printer, people)

        return  Person(purchase)

class VisitorService(object):
    def __init__(self, badges=None):
        self.badges = badges or BadgeService()

    def create(self, printer, by_user=None, **data):

        parsed_data, errors = schema.VisitorSchema().load(data)
        if errors:
            raise SchemaValidationError(errors)

        if not printer: raise MustSpecifyPrinter()
        visitor = Visitor(**parsed_data)
        db.session.add(visitor)
        db.session.commit()
        self.badges.make_badge(printer, visitor, by_user=by_user)
        return visitor


class ReportService(object):
    def __init__(self, payments=None):
        self.payments = payments or CashPaymentService()

    def for_cashier(self, cashier, date):
        return self.payments.for_cashier(cashier, date)

class PeopleService(object):
    def __init__(self, purchases=None, filters=None, products=None, promocodes=None,
                       accounts=None, hasher=None, mailer=None, cash=None):
        self.products   = products   or ProductService()
        self.purchases  = purchases  or PurchaseService()
        self.accounts   = accounts   or AccountService()
        self.filters    = filters    or FrontDeskFilterStrategies()
        self.hasher     = hasher     or Hasher()
        self.mailer     = mailer     or MailerService()
        self.cash       = cash       or PaymentService()
        self.promocodes = promocodes or PromoCodePaymentService()

    def get_by_hash(self, hash_code):
        purchase = self.purchases.get_by_hash(hash_code, strict=True)
        return Person(purchase)

    def pay(self, person_id, by_user, ip_address=None, mode=None):
        if not mode:       raise InvalidPaymentOperation('ip_address')
        if not ip_address: raise InvalidPaymentOperation('mode')

        # retrieves purchase, creates a new cash payment (ignores instructions (_))
        purchase   = self.purchases.get_one(person_id, strict=True, check_ownership=False)
        _, payment = self.cash.create(purchase, 'cash', None)

        # prepares payload for processor and notifies transition
        payload = dict(cashier=by_user, ip_address=ip_address, mode=mode)
        purchase, transition = self.cash.notify(purchase.id, payment.id, payload, source='frontdesk')

        return Person(purchase)

    def add_product(self, customer_id, product=None, by_user=None):
        '''Add a new purchase to the account and return a person object'''
        from segue.models import Account

        account = Account.query.filter(Account.id==customer_id).first()

        default_product = product or self.products.chepest_available_for('normal')
        purchase = Purchase(customer=account, product=default_product)
        purchase.qty = 1
        purchase.amount = default_product.price
        purchase.due_date = default_product.due_date

        db.session.add(purchase)
        db.session.commit()

        return Person(purchase)


    def send_reception_mail(self, person_id):
        purchase = self.purchases.get_one(person_id, strict=True, check_ownership=False)

        if not purchase.hash_code:
            purchase.hash_code = self.hasher.generate()
            db.session.add(purchase)
            db.session.commit()

        person = Person(purchase)
        self.mailer.reception_mail(person)
        return person

    def by_range(self, start, end):
        purchases = self.purchases.by_range(start, end).all()
        return map(Person, purchases)

    def get_one(self, person_id, by_user=None, check_ownership=True, strict=True):
        purchase = self.purchases.get_one(person_id, by=by_user, strict=True, check_ownership=check_ownership)
        if purchase: return Person(purchase)
        if strict: raise NoSuchPurchase()
        return None

    def _get_customer(self, employer_id):
        purchase = self.purchases.get_one(employer_id, by=None, strict=True, check_ownership=False)
        if purchase:
            return purchase.customer
        else:
            raise NoSuchPurchase()

    def _create_employee_relationship(self, employer_id, person_id):
        employer = self._get_customer(employer_id)
        employee = self._get_customer(person_id)

        employee.corporate_id = employer.corporate_owned.id
        db.session.add(employee)
        db.session.commit()

    def lookup(self, needle, by_user=None, limit=20):
        base    = self.filters.all_joins(Purchase.query)
        filters = self.filters.needle(needle)
        query   = base.filter(*filters).order_by(Purchase.status, Purchase.id).limit(limit)
        return map(Person, query.all())

    def apply_promo(self, person_id, promo_hash, by_user=None):
        person  = self.get_one(person_id, by_user=by_user, strict=True)
        if person.is_valid_ticket: raise PurchaseAlreadySatisfied()
        if not person.can_change_product: raise CannotChangeProduct()

        self.promocodes.create(person.purchase, dict(hash_code=promo_hash), commit=False, force_product=True)
        db.session.commit()
        db.session.expunge_all()

        return self.get_one(person_id, strict=True, check_ownership=False)

    def list_promocodes(self, person_id, by_user=None):
        pass


    def register_employee(self, employer_id, by_user=None, **data):

        employer = self._get_customer(employer_id)

        promo_hash = data.get('promo_hash', None)
        product = self.products.cheapest_for('corporate-promocode')

        person = self.create(data, by_user=by_user, product=product)
        person = self.patch_address(person.id, by_user=by_user, **data)

        self._create_employee_relationship(employer_id, person.id)

        return self.apply_promo(person.id, promo_hash, by_user=by_user)

    def set_donation(self, person_id, new_product_id, amount, by_user=None):
        person = self.get_one(person_id, by_user=by_user, strict=True)
        purchase = person.purchase
        product  = self.products.get_product(new_product_id)
        buyer    = BuyerFactory().from_account(person.purchase.customer)

        if purchase.satisfied:
            raise CannotChangeProduct()

        purchase.buyer = buyer
        purchase.product = product
        if product.price == 0:
            purchase.amount = amount
        else:
            purchase.amount = product.price

        db.session.add(purchase)
        db.session.commit()
        db.session.expunge_all()

        return self.get_one(person_id, strict=True, check_ownership=False)


    def set_product(self, person_id, new_product_id, qty,  by_user=None):
        person   = self.get_one(person_id, by_user=by_user, strict=True)
        purchase = person.purchase
        product  = self.products.get_product(new_product_id)
        buyer    = BuyerFactory().from_account(person.purchase.customer)


        if not person.can_change_product:
            raise CannotChangeProduct()
        if not product.check_eligibility({}, purchase.customer):
            raise WrongBuyerForProduct()

        #TODO: FIX POPULATE BUYER TABLE
        purchase.buyer = buyer
        purchase.product = product
        purchase.amount = product.price
        purchase.qty = qty
        purchase.due_date = product.due_date

        #HACK
        if product.special_purchase_class():
            purchase.kind = product.special_purchase_class().__mapper_args__['polymorphic_identity']
        else:
            purchase.kind = purchase.kind

        db.session.add(purchase)
        db.session.commit()
        db.session.expunge_all()

        return self.get_one(person_id, strict=True, check_ownership=False)


    def new_donation(self, customer_id, product=None, by_user=None):

        account = self.accounts.get_one(customer_id,check_ownership=False)
        default_product = product or self.products.cheapest_for('donation')
        purchase = Purchase(customer=account, product=default_product)

        purchase.qty = 1
        purchase.amount = default_product.price
        db.session.add(purchase)
        db.session.commit()

        return Person(purchase)

    def get_employeer(self, customer_id, by_user=None):
        return  self.accounts.get_one(customer_id, strict=True, check_ownership=False)

    def create(self, data, by_user=None, product=None):
        #_validate('create', dict(email=email))

        try:
            logger.error(data)
            account = self.accounts.create_people(data)
        except Exception as ex:
            logger.error(ex)

        default_product = product or self.products.chepest_available_for('normal')
        print(default_product)
        logger.error(account)

        logger.error(default_product)

        purchase = Purchase(customer=account, product=default_product)
        purchase.qty = 1
        purchase.amount = default_product.price
        purchase.due_date = default_product.due_date

        db.session.add(purchase)
        db.session.commit()
        logger.error(purchase)

        return Person(purchase)

    def patch_badge(self, person_id, by_user=None, **data):
        purchase = self.purchases.get_one(person_id, by=by_user, strict=True)
        customer = purchase.customer

        parsed_data, errors = schema.BadgeSchema().load(data)
        if errors:
            raise SchemaValidationError(errors)

        purchase.customer.badge_name = parsed_data['badge_name']
        purchase.customer.organization = parsed_data['badge_corp']

        db.session.add(purchase.customer)
        db.session.commit()

        return Person(purchase)

    def patch_info(self, person_id, by_user=None, **data):
        purchase = self.purchases.get_one(person_id, by=by_user, strict=True)
        customer = purchase.customer

        parsed_data, errors = schema.PeopleSchema().load(data)
        if errors:
            raise SchemaValidationError(errors)

        for name, value in parsed_data.items():
            setattr(customer, name, value)

        db.session.add(purchase.customer)
        db.session.commit()

        return Person(purchase)


    def patch_address(self, person_id, by_user=None, **data):
        purchase = self.purchases.get_one(person_id, by=by_user, strict=True)
        customer = purchase.customer

        parsed_data, errors = schema.PeopleAddressSchema().load(data)
        #if errors:
        #    raise SchemaValidationError(errors)

        for name, value in parsed_data.items():
            setattr(customer, name, value)

        db.session.add(purchase.customer)
        db.session.commit()

        return Person(purchase)

    def patch(self, person_id, by_user=None, **data):
        purchase = self.purchases.get_one(person_id, by=by_user, strict=True)

        _validate('patch', data)

        for key, value in data.items():
            method = getattr(self, "_patch_"+key, None)
            if method: method(purchase, value)

        db.session.add(purchase)
        db.session.commit()

        return Person(purchase)

    def _patch_name(self, purchase, value):
        purchase.customer.name = value
        db.session.add(purchase.customer)

    def _patch_address_city(self, purchase, value):
        purchase.customer.city = value
        db.session.add(purchase.customer)

    def _patch_document(self, purchase, value):
        purchase.customer.document = value
        db.session.add(purchase.customer)

    def _patch_country(self, purchase, value):
        purchase.customer.country = value
        db.session.add(purchase.customer)

    def _patch_badge_name(self, purchase, value):
        purchase.customer.badge_name = value
        db.session.add(purchase.customer)

    def _patch_badge_corp(self, purchase, value):
        if not purchase.can_change_badge_corp: return
        purchase.customer.organization = value
        db.session.add(purchase.customer)
