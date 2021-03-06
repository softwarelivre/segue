# -*- coding: utf-8 -*-

import flask
from flask.ext.jwt import current_user
from flask import request

from segue.json import JsonFor
from segue.core import config
from segue.decorators import jsoned, jwt_only, admin_only
from segue.schema import Field

from segue.document.services import DocumentService
from segue.hasher import Hasher
from services import PurchaseService, PaymentService, PromoCodeService
from factories import PurchaseFactory
from responses import GuideResponse, PromoCodeResponse, PromoCodeListResponse
from segue.purchase.services import ProcessBoletosService
from segue.responses import Response
from promocode.factories import PromoCode
from flask import request, url_for, redirect
from webargs.flaskparser import parser
import schema


class PurchaseController(object):
    def __init__(self, service=None, payments=None, hash=None, documents=None):
        self.service = service or PurchaseService()
        self.payments = payments or PaymentService()
        self.hash = hash or Hasher(10)
        self.documents = documents or DocumentService()
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
    @jwt_only
    def upload_buyer_document(self, purchase_id):
        #TODO: IMPROVE
        from segue.document.services import DocumentService

        data = request.get_json()
        purchase = self.service.get_one(purchase_id, by=current_user)
        doc = data.get('document_file', None)
        if doc and purchase:
            document_file_hash = self.hash.generate()
            self.documents.base64_to_pdf('buyer-document', document_file_hash, doc)
            self.payments.on_gov_document_received(purchase, document_file_hash)
            return 200
        else:
            return 404



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

    @jwt_only
    @jsoned
    def check_promocode(self, hash=None):
        from segue.purchase.errors import BlockedDiscount
        result = self.service.check_promocode(hash, by=self.current_user) or flask.abort(404)
        #HACK
        if result and result.discount != 1.0 and self.service.current_mode() != 'online':
            raise BlockedDiscount()

        return Response(result, PromoCodeResponse).create(), 200

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

    @jsoned
    def paypal_notify(self, purchase_id=None, payment_id=None):
        payload = request.args.to_dict(True)
        result = self.service.notify(purchase_id, payment_id, payload) or flask.abort(404)
        conclude = url_for('purchase_payments.conclude', purchase_id=purchase_id, payment_id=payment_id)
        conclude_url = conclude + '?token={}'.format(payload.get('token', ''))
        return redirect(conclude_url)

    def conclude(self, purchase_id, payment_id):
        payload = request.args.to_dict(True)
        purchase = self.service.conclude(purchase_id, payment_id, payload)
        if not purchase:
            flask.abort(404)
        else:
            base_path = 'purchase'
            if purchase.product.category == 'donation':
                base_path = 'donation'
            path = '/#/{}/{}/payment/{}/conclude'.format(base_path, purchase_id, payment_id)
            return flask.redirect(config.FRONTEND_URL + path)


class PromocodeController(object):
    def __init__(self, service=None):
        self.service = service or PromoCodeService()

    @jsoned
    @jwt_only
    def list(self):
        parms = parser.parse({
            'creator_id': Field.int(),
            'purchase_id': Field.int()
            },
            request
        )

        result = self.service.query(**parms)
        return Response(result, PromoCodeListResponse).create(), 200