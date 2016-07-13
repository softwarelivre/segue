from datetime import datetime
from segue.core import config, db

from flask import request, abort, redirect
from flask.ext.jwt import current_user
from segue.decorators import jwt_only, frontdesk_only, jsoned, accepts_html, cashier_only

from services import BadgeService, PeopleService, VisitorService, ReportService, SpeakerService
from responses import PersonResponse, BadgeResponse, BuyerResponse, ProductResponse, PaymentResponse, ReceptionResponse, VisitorResponse, EmployeerResponse, EmployeeResponse

class VisitorController(object):
    def __init__(self, visitors=None):
        self.visitors     = visitors or VisitorService()
        self.current_user = current_user

    @jwt_only
    @frontdesk_only
    @jsoned
    def create(self):
        data = request.get_json()
        printer = data.pop('printer',None)
        visitor = self.visitors.create(printer, by_user=self.current_user, **data)
        return VisitorResponse.create(visitor), 200

class PrinterController(object):
    def __init__(self, visitors=None):
        self.current_user = current_user

    @jwt_only
    @frontdesk_only
    @jsoned
    def list(self):
        return config.PRINTERS

class ReceptionController(object):
    def __init__(self, people=None):
        self.people = people or PeopleService()

    @jsoned
    @accepts_html
    def get_by_hash(self, hash_code=None, wants_html=False):
        person = self.people.get_by_hash(hash_code) or flask.abort(404)
        if wants_html:
            path = '/#/reception/{}'.format(hash_code)
            return redirect(config.FRONTEND_URL + path)
        else:
            return ReceptionResponse.create(person), 200

class PersonController(object):
    def __init__(self, people=None, badges=None):
        self.people = people or PeopleService()
        self.badges = badges or BadgeService()
        self.current_user = current_user

    @jwt_only
    @frontdesk_only
    @jsoned
    def list(self):
        needle = request.args.get('q')
        result = self.people.lookup(needle, by_user=self.current_user)
        return PersonResponse.create(result, links=True), 200

    @jwt_only
    @frontdesk_only
    @jsoned
    def get_one(self, person_id):
        result = self.people.get_one(person_id, by_user=self.current_user)
        return PersonResponse.create(result, links=True, embeds=True), 200

    @jwt_only
    @frontdesk_only
    @jsoned
    def patch(self, person_id):
        data = request.get_json()
        result = self.people.patch(person_id, by_user=self.current_user, **data)
        return {}, 200

    @jwt_only
    @frontdesk_only
    @jsoned
    def patch_info(self, person_id):
        data = request.get_json()
        result = self.people.patch_info(person_id, by_user=self.current_user, **data)
        return {}, 200

    @jwt_only
    @frontdesk_only
    @jsoned
    def patch_address(self, person_id):
        data = request.get_json()
        result = self.people.patch_address(person_id, by_user=self.current_user, **data)
        return {}, 200

    @jwt_only
    @frontdesk_only
    @jsoned
    def patch_badge(self, person_id):
        data = request.get_json()
        result = self.people.patch_badge(person_id, by_user=self.current_user, **data)
        return {}, 200


    @jwt_only
    @cashier_only
    @jsoned
    def add_product(self, customer_id):
        data = request.get_json()
        result = self.people.add_product(customer_id, by_user=self.current_user)
        return PersonResponse.create(result, embeds=False, links=False), 200

    @jwt_only
    @cashier_only
    @jsoned
    def register_employee(self, employer_id):
        data = request.get_json()
        result = self.people.register_employee(employer_id, by_user=self.current_user, **data)
        return {}, 200

    @jwt_only
    @frontdesk_only
    @jsoned
    def create(self):
        data = request.get_json()
        result = self.people.create(data, by_user=self.current_user)
        return PersonResponse.create(result, embeds=False, links=False), 200

    @jwt_only
    @frontdesk_only
    @jsoned
    def apply_promo(self, person_id):
        promo_hash = request.get_json().get('hash_code',None)
        if not promo_hash: abort(400)
        result = self.people.apply_promo(person_id, promo_hash, by_user=self.current_user)
        return {}, 200

    @jwt_only
    @cashier_only
    @jsoned
    def make_payment(self, person_id):
        data = request.get_json()
        result = self.people.pay(person_id, by_user=self.current_user, ip_address=request.remote_addr, **data)
        return {}, 200


    @jwt_only
    @frontdesk_only
    @jsoned
    def make_donation_payment(self, person_id):
        data = request.get_json()
        result = self.people.pay(person_id, by_user=self.current_user, ip_address=request.remote_addr, **data)
        return {}, 200

    @jwt_only
    @frontdesk_only
    @jsoned
    def set_product(self, person_id):
        new_product_id = request.get_json().get('product_id',None)
        qty = request.get_json().get('qty', 1)
        if not new_product_id: abort(400)
        result = self.people.set_product(person_id, new_product_id, qty, by_user=self.current_user)
        return {}, 200

    @jwt_only
    @frontdesk_only
    @jsoned
    def eligible(self, person_id):
        result = self.people.get_one(person_id, by_user=self.current_user) or abort(404)
        return ProductResponse.create(result.eligible_products), 200

    @jwt_only
    @frontdesk_only
    @jsoned
    def eligible_donation(self, person_id):
        result = self.people.get_one(person_id, by_user=self.current_user) or abort(404)
        return ProductResponse.create(result.eligible_donation_products), 200

    @jwt_only
    @frontdesk_only
    @jsoned
    def new_donation(self, customer_id):
        result = self.people.new_donation(customer_id, by_user=self.current_user) or abort(404)
        return PersonResponse.create(result), 200

    @jwt_only
    @frontdesk_only
    @jsoned
    def change_donation(self, person_id):
        new_product_id = request.get_json().get('product_id') or abort(404)
        amount = request.get_json().get('amount', 10)

        result = self.people.set_donation(person_id, new_product_id, amount, by_user=self.current_user)
        return {}, 200


    @jwt_only
    @frontdesk_only
    @jsoned
    def get_employeer(self, customer_id):
        result = self.people.get_employeer(customer_id, by_user=self.current_user)
        return EmployeerResponse.create(result), 200

    @jwt_only
    @jsoned
    def promocodes_list(self, person_id):
        person_id = request.get_json().get('product_id') or abort(404)

        person = self.people.get_one(person_id, by_user=self.current_user)

        print(person.promocodes)

        return {}, 200


    @jwt_only
    @frontdesk_only
    @jsoned
    def buyer(self, person_id):
        result = self.people.get_one(person_id, by_user=self.current_user) or abort(404)
        return BuyerResponse.create(result.buyer), 200

    @jwt_only
    @frontdesk_only
    @jsoned
    def related(self, person_id):
        result = self.people.get_one(person_id, by_user=self.current_user) or abort(404)
        return PersonResponse.create(result.related_people, links=False), 200

    def get_badge(self, person_id):
        pass

    @jwt_only
    @frontdesk_only
    @jsoned
    def create_badge(self, person_id):
        printer = request.get_json().get('printer',None)
        if not printer: abort(400)

        person = self.people.get_one(person_id, by_user=self.current_user)
        result = self.badges.make_badge(printer, person, by_user=self.current_user)

        return {},200

    @jwt_only
    @frontdesk_only
    @jsoned
    def list_employees(self, person_id):
        # TODO: REMOVE
        from segue.responses import Response
        from segue.account.models import Account
        from segue.purchase.promocode.models import PromoCodePayment, PromoCode
        from segue.purchase.models import Purchase

        customer_id = db.session.query(Purchase.customer_id).filter(Purchase.id==person_id).subquery()

        result = db.session.query(PromoCodePayment) \
            .join(Purchase) \
            .join(Account) \
            .filter(PromoCodePayment.promocode_id.in_(
            db.session.query(PromoCode.id).filter(PromoCode.creator_id == customer_id))).all()

        if result:
            return EmployeeResponse.create(result), 200
        return [], 200



class SpeakerController(object):
    def __init__(self, badges=None, speakers=None):
        self.badges = badges or BadgeService()
        self.speakers = speakers or SpeakerService()
        self.current_user = current_user

    @jwt_only
    @frontdesk_only
    @jsoned
    def create(self):
        data = request.get_json()
        printer = data.pop('printer') or abort(400)
        ticket = data.pop('ticket') or abort(400)

        speaker = self.speakers.create(ticket=ticket, printer=printer, by_user=self.current_user, **data)
        return PersonResponse.create(speaker), 200


class BadgeController(object):
    def __init__(self, badges=None):
        self.badges       = badges or BadgeService()
        self.current_user = current_user

    @jwt_only
    @frontdesk_only
    @jsoned
    def give(self, badge_id):
        badge = self.badges.give_badge(badge_id) or abort(404)
        return BadgeResponse.create(badge), 200


DATE_FORMAT = "%Y-%m-%d"
class ReportController(object):
    def __init__(self, reports=None):
        self.reports = reports or ReportService()
        self.current_user = current_user

    @jwt_only
    @cashier_only
    @jsoned
    def get_report(self, date=None):
        date = datetime.strptime(date,DATE_FORMAT) if date else datetime.now()
        result = self.reports.for_cashier(self.current_user, date=date)
        return PaymentResponse.create(result, transitions=True, person=True), 200
