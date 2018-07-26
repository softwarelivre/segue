from flask import request, abort
from flask.ext.jwt import current_user
from webargs.flaskparser import parser, use_args

from segue.helpers import search_args
from segue.responses import Response
from segue.schema import Field
from segue.decorators import jsoned, admin_only, jwt_only

from segue.account.services import AccountService

from segue.caravan.responses import CaravanResponse, CaravanListResponse, CaravanInviteResponse
from segue.caravan.services import CaravanService, CaravanInviteService
from segue.caravan.models import Caravan


class AdminCaravanController(object):

    def __init__(self, caravans=None, accounts=None):
        self.caravans = caravans or CaravanService()
        self.accounts = accounts or AccountService()
        self.current_user = current_user

    @jsoned
    @jwt_only
    @admin_only
    @use_args(search_args)
    def list_caravans(self, args):
        criteria = parser.parse({
            'caravan_name': Field.str(),
            'owner_name': Field.str()
        }, request)
        
        result = self.caravans.lookup(criteria, page=args['page'], per_page=args['per_page'])

        return Response(result, CaravanListResponse).create(), 200

    @jsoned
    @jwt_only
    @admin_only
    def exempt_leader(self, caravan_id):
        self.caravans.exempt_leader(caravan_id)
        return {}, 200

    @jwt_only
    @admin_only
    @jsoned
    def get_one(self, caravan_id):
        result = self.caravans.get_one(caravan_id, by=current_user)
        return Response(result, CaravanResponse).create(), 200

    @jsoned
    @jwt_only
    @admin_only
    def create(self):
        data = request.get_json()
        owner_id = data.get('owner_id', None) or abort(404)
        owner = self.accounts.get_one(owner_id, check_ownership=False)
        result = self.caravans.create(data, owner)
        return Response(result, CaravanResponse).create(), 200


    @jsoned
    @jwt_only
    @admin_only
    def modify(self, caravan_id):
        data = request.get_json()
        owner_id = data.get('owner_id', None) or abort(404)
        owner = self.accounts.get_one(owner_id, check_ownership=False)
        result = self.caravans.modify(caravan_id, data, owner, by=owner)
        return result, 200


class AdminCaravanInviteController(object):
    def __init__(self, service=None):
        self.service = service or CaravanInviteService()
        self.current_user = current_user

    @jsoned
    @jwt_only
    @admin_only
    def list(self, caravan_id):
        result = self.service.list(caravan_id, by=self.current_user)
        return Response(result, CaravanInviteResponse).create(), 200

    @jsoned
    @jwt_only
    @admin_only
    def send_invite(self, caravan_id, hash_code):
        self.service.send_invite(hash_code)
        return {}, 200


    @jwt_only
    @admin_only
    @jsoned
    def create(self, caravan_id):
        data = request.get_json()
        result = self.service.create(caravan_id, data, by=self.current_user, send_email=False)
        return result, 200

    @jwt_only
    @admin_only
    @jsoned
    def edit(self, caravan_id, invite_id):
        data = request.get_json()
        result = self.service.create(caravan_id, data, by=self.current_user, send_email=False)
        return result, 200

    @jwt_only
    @admin_only
    @jsoned
    def accept(self, caravan_id, hash_code):
        result = self.service.accept_invite(hash_code) or abort(404)
        return result, 200

    @jwt_only
    @admin_only
    @jsoned
    def decline(self, caravan_id, hash_code):
        result = self.service.decline_invite(hash_code) or abort(404)
        return result, 200

    @jwt_only
    @admin_only
    @jsoned
    def delete(self, caravan_id, hash_code):
        self.service.delete(hash_code)
        return {}, 200
