import flask
from flask import request
from flask.ext.jwt import current_user, verify_jwt, JWTError

from segue.core import config
from segue.json import JsonFor
from segue.decorators import jsoned, jwt_only, accepts_html

import schema

from services import CaravanService, CaravanInviteService

class CaravanController(object):
    def __init__(self, service=None):
        self.service = service or CaravanService()
        self.current_user = current_user

    @jwt_only
    @jsoned
    def create(self):
        data = request.get_json()
        return self.service.create(data, self.current_user), 201

    @jwt_only
    @jsoned
    def modify(self, caravan_id):
        data = request.get_json()
        owner = self.current_user
        result = self.service.modify(caravan_id, data, owner, by=owner) or flask.abort(404)
        return result, 200

    @jwt_only
    @jsoned
    def get_one(self, caravan_id=None):
        if caravan_id:
            result = self.service.get_one(caravan_id, self.current_user) or flask.abort(404)
        else:
            owner_id = int(request.args.get('owner_id', self.current_user.id))
            result = self.service.get_by_owner(owner_id, self.current_user)
        return result, 200

    @jsoned
    def schema(self, name):
        return schema.whitelist[name], 200

class CaravanInviteController(object):
    def __init__(self, service=None):
        self.service = service or CaravanInviteService()
        self.current_user = current_user

    @jwt_only
    @jsoned
    def list(self, caravan_id):
        result = self.service.list(caravan_id, by=self.current_user)
        return JsonFor(result).using('ShortCaravanInviteJsonSerializer'), 200

    @jsoned
    @accepts_html
    def get_by_hash(self, caravan_id, hash_code, wants_html=False):
        invite = self.service.get_by_hash(hash_code) or flask.abort(404)
        if wants_html:
            path = '/#/caravan/{}/invite/{}/answer'.format(caravan_id, hash_code)
            return flask.redirect(config.FRONTEND_URL + path)
        else:
            return invite, 200

    @jwt_only
    @jsoned
    def create(self, caravan_id):
        data = request.get_json()
        result = self.service.create(caravan_id, data, by=self.current_user)
        return result, 200

    @jwt_only
    @jsoned
    def accept(self, caravan_id, hash_code):
        result = self.service.accept_invite(hash_code, by=self.current_user) or flask.abort(404)
        return result, 200

    @jwt_only
    @jsoned
    def decline(self, caravan_id, hash_code):
        result = self.service.decline_invite(hash_code, by=self.current_user) or flask.abort(404)
        return result, 200

    @jsoned
    def register(self, caravan_id, hash_code):
        data = request.get_json()
        result = self.service.register(hash_code, data) or flask.abort(404)
        return result, 200
