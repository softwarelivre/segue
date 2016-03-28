

from flask.ext.jwt import current_user


from segue.decorators import jwt_only, admin_only, jsoned
from segue.product.services import ProductService
from segue.json import JsonFor


class AdminProductController(object):
    def __init__(self, products=None):
        self.products    = products or ProductService()
        self.current_user = current_user

    @jsoned
    @jwt_only
    @admin_only
    def list(self):
        result = self.products.all()
        return JsonFor(result).using('ProductJsonSerializer'), 200