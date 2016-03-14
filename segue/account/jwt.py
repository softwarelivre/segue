from ..core import jwt
from flask import current_app
from werkzeug.local import LocalProxy
from schema import AccountTokenSchema

local_jwt = LocalProxy(lambda: current_app.extensions['jwt'])

@jwt.user_handler
def load_user(payload):
    from services import AccountService
    if payload["id"]:
        return AccountService().get_one(payload["id"], check_ownership=False)

class Signer(object):
    def __init__(self, jwt=local_jwt, serializer=None):
        self.jwt = jwt
        self.serializer = serializer or AccountTokenSchema()

    def sign(self, account):
        token = self.jwt.encode_callback(self.serializer.serialize(account))
        return {
            "credentials": self.serializer.serialize(account),
            "token": token
        }


