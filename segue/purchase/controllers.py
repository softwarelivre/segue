import flask
from flask.ext.jwt import current_user
from flask import request

from segue.json import JsonFor
from segue.core import config
from segue.decorators import jsoned, jwt_only, admin_only

from services import PurchaseService, PaymentService, PromoCodeService
from factories import PurchaseFactory
from responses import GuideResponse, PromoCodeResponse, PromoCodeListResponse
from segue.purchase.services import ProcessBoletosService
from segue.responses import Response
from promocode.factories import PromoCode
import schema

class PurchaseController(object):
    def __init__(self, service=None):
        self.service = service or PurchaseService()
        self.current_user = current_user

    @jsoned
    @jwt_only
    @admin_only
    def process_boletos(self):
        file = request.files['file']
        if file:
            processor = ProcessBoletosService()
            result = processor.process(file.read())
            return dict(payments=result), 200

        return 200

    @jsoned
    def current_mode(self):
        return { 'mode': self.service.current_mode() }, 200

    @jsoned
    @jwt_only
    def list(self):
        parms = { c: request.args.get(c) for c in PurchaseFactory.QUERY_WHITELIST if c in request.args }
        result = self.service.query(by=self.current_user, **parms)
        return JsonFor(result).using('PurchaseJsonSerializer'), 200

    @jwt_only
    @jsoned
    def get_one(self, purchase_id=None):
        result = self.service.get_one(purchase_id, by=self.current_user) or flask.abort(404)
        return result, 200

    @jwt_only
    @jsoned
    def pay(self, purchase_id=None, method=None):
        payload = request.get_json()
	#FIX - Find a better solution
        #if method != 'cash': return {}, 400
        result = self.service.create_payment(purchase_id, method, payload, by=self.current_user)
        return result, 200

    @jsoned
    def schema(self, name):
        return schema.whitelist[name], 200

    @jwt_only
    @jsoned
    def clone(self, purchase_id=None):
        result = self.service.clone_purchase(purchase_id, by=self.current_user) or flask.abort(404)
        return result, 200

    @jsoned
    def check_promocode(self, hash=None):
        result = self.service.check_promocode(hash, by=self.current_user) or flask.abort(404)
        return PromoCodeResponse(result), 200

    @jsoned
    def donations_count(self):
        #TODO: FIX
        from segue.core import db
        from segue.models import Purchase
        from segue.models import Product
        from sqlalchemy import func

        result = db.session.query(func.count(Purchase.id))\
            .join(Product).filter(Purchase.status=='paid')\
            .filter(Product.category=='donation')\
            .scalar() or 0

        return {'total': result}



class PaymentController(object):
    def __init__(self, service=None):
        self.service = service or PaymentService()
        self.current_user = current_user

    @jsoned
    @jwt_only
    def guide(self, purchase_id=None, payment_id=None):
        payment = self.service.get_one(purchase_id, payment_id) or flask.abort(404)
        if payment.purchase.customer != self.current_user:
            flask.abort(401)
        return GuideResponse(payment), 200

    @jsoned
    def notify(self, purchase_id=None, payment_id=None):
        payload = request.form.to_dict(True)
        result = self.service.notify(purchase_id, payment_id, payload) or flask.abort(404)
        return result[0], 200

    def conclude(self, purchase_id, payment_id):
        payload = request.args.to_dict(True)
        self.service.conclude(purchase_id, payment_id, payload) or flask.abort(404)
        path = '/#/purchase/{}/payment/{}/conclude'.format(purchase_id, payment_id)
        return flask.redirect(config.FRONTEND_URL + path)


class PromocodeController(object):
    def __init__(self, service=None):
        self.service = service or PromoCodeService()

    @jsoned
    @jwt_only
    def list(self):
        #TODO: CHECK PARAMETERS
        parms = {c: request.args.get(c) for c in ['creator_id'] if c in request.args}
        result = self.service.query(**parms)
        return Response(result, PromoCodeListResponse).create(), 200