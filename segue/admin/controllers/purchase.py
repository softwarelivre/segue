

from flask import request, abort
from flask.ext.jwt import current_user
from webargs.flaskparser import parser

from segue.decorators import jwt_only, admin_only, jsoned
from segue.purchase.services import PurchaseService, PaymentService
from segue.purchase.models import Purchase

from segue.responses import Response
from segue.schema import Field
from schemas import PurchaseDetail



class AdminPurchaseController(object):
    def __init__(self, purchases=None, payments=None):
        self.purchases    = purchases or PurchaseService()
        self.payments     = payments or PaymentService()
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

