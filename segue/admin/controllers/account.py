import json

from flask import request, abort
from flask.ext.jwt import current_user

from segue.decorators import jwt_only, admin_only, jsoned
from segue.account.services import AccountService
from segue.purchase.services import PurchaseService

from ..responses import AccountDetailResponse, ProposalDetailResponse

from segue.responses import Response
from schemas import AccountDetail
from segue.schema import Field


from flask import request
from webargs.flaskparser import parser

class AdminAccountController(object):
    def __init__(self, accounts=None, purchases=None):
        self.accounts     = accounts or AccountService()
        self.purchases    = purchases or PurchaseService()
        self.current_user = current_user

    @jwt_only
    @admin_only
    @jsoned
    def create(self):
        data = request.get_json()
        result = self.accounts.create(data)
        return Response(result, AccountDetail).create(), 200

    @jwt_only
    @admin_only
    @jsoned
    def modify(self, account_id):
        data = request.get_json()
        result = self.accounts.modify(account_id, data, by=self.current_user, allow_email_change=True) or flask.abort(404)
        return result, 200

    @jsoned
    @jwt_only
    @admin_only
    def list(self):
        args = parser.parse({
                'id': Field.int(),
                'name': Field.str(),
                'email': Field.str(),
                'document': Field.str(),
                'purchase_id': Field.int(),
                'product_id': Field.int()
            },
            request
        )
        result = self.accounts.lookup(criteria=args, limit=20)
        return Response(result, AccountDetail).create(), 200

    @jsoned
    @jwt_only
    @admin_only
    def get_one(self, account_id=None):
        result = self.accounts.get_one(account_id, check_ownership=False) or abort(404)
        return Response(result, AccountDetail).create(), 200

    @jsoned
    @jwt_only
    @admin_only
    def proposals_of_account(self, account_id=None):
        account = self.accounts.get_one(account_id, by=self.current_user) or abort(404)
        return ProposalDetailResponse.create(account.all_related_proposals), 200

    @jsoned
    @jwt_only
    @admin_only
    def get_by_purchase(self, purchase_id=None):
        result = self.purchases.get_one(purchase_id, by=self.current_user) or abort(404)
        return AccountDetailResponse(result.customer), 200
