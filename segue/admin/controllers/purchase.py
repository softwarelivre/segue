import json

from flask import request, abort, jsonify
from flask.ext.jwt import current_user
from webargs.flaskparser import parser

from segue.decorators import jwt_only, admin_only, jsoned
from segue.purchase.services import PurchaseService, PaymentService, AdempiereService
from segue.purchase.models import Purchase

from segue.responses import Response
from segue.schema import Field
from schemas import PurchaseDetail



class AdminPurchaseController(object):
    def __init__(self, purchases=None, payments=None, adempiere=None):
        self.purchases    = purchases or PurchaseService()
        self.payments     = payments or PaymentService()
        self.adempiere = AdempiereService()
        self.current_user = current_user

    @jsoned
    @jwt_only
    @admin_only
    def list(self):
        args = parser.parse({
                'id': Field.int(),
                'customer_name': Field.str(),
                'customer_id': Field.int(),
                'status': Field.str(),
                'product_id': Field.int()
            },
            request
        )

        result = self.purchases.lookup(criteria=args)
        return Response(result, PurchaseDetail).create(), 200

    @jsoned
    @jwt_only
    @admin_only
    def confirm_student_document(self, purchase_id):
        #TODO: REVIEW
        pur = Purchase.query.filter(Purchase.id == purchase_id).first()
        if pur and self.payments.on_finished_student_document_analysis(pur):
            return '', 204
        abort(400)

    @jsoned
    @jwt_only
    @admin_only
    def confirm_gov_document(self, purchase_id):
        #TODO: REVIEW
        pur = Purchase.query.filter(Purchase.id == purchase_id).first()
        if pur and self.payments.on_gov_document_analyzed(pur):
            return '', 204
        abort(400)


    @jwt_only
    @admin_only
    def adempiere_report(self):
        args = parser.parse({
            'initial_date': Field.date(),
            'end_date': Field.date()
            },
            request
        )
        report_data = self.adempiere.generate_report(args['initial_date'], args['end_date'])

        #TODO: FIX
        return json.dumps({'report_data':report_data}, default=json_encode_decimal), 200



#TODO: REMOVE
def json_encode_decimal(obj):
    from decimal import Decimal
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(repr(obj) + " is not JSON serializable")