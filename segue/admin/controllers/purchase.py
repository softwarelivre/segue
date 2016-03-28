

from flask import request
from flask.ext.jwt import current_user
from webargs.flaskparser import parser

from segue.decorators import jwt_only, admin_only, jsoned
from segue.purchase.services import PurchaseService

from segue.responses import Response
from segue.schema import Field
from schemas import PurchaseDetail




class AdminPurchaseController(object):
    def __init__(self, purchases=None):
        self.purchases    = purchases or PurchaseService()
        self.current_user = current_user

    @jsoned
    @jwt_only
    @admin_only
    def list(self):
        args = parser.parse({
                'id': Field.int(),
                'customer_name': Field.str(),
                'status': Field.str(),
                'product_id': Field.int()
            },
            request
        )

        result = self.purchases.lookup(criteria=args, limit=20)
        return Response(result, PurchaseDetail).create(), 200
