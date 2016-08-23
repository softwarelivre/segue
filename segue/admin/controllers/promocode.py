from flask import request, abort
from flask.ext.jwt import current_user

from webargs.flaskparser import parser, use_args


from segue.helpers import search_args
from segue.responses import Response
from segue.schema import Field
from segue.core import cache
from segue.decorators import jsoned, jwt_only, admin_only

from segue.purchase.promocode import PromoCodeService
from segue.product.services import ProductService
from segue.errors import SchemaValidationError


from ..responses import PromoCodeResponse, ProductDetailResponse, PromoCodeListResponse
from babel.util import missing

class AdminPromoCodeController(object):
    def __init__(self, promocodes=None, products=None):
        self.current_user = current_user
        self.promocodes   = promocodes or PromoCodeService()
        self.products     = products   or ProductService()

    @jwt_only
    @admin_only
    @jsoned
    @use_args(search_args)
    def list_promocodes(self, args):
        criteria = parser.parse({
            'hash_code': Field.str(),
            'description': Field.str()
        }, request)

        result = self.promocodes.lookup(criteria=criteria, page=args['page'], per_page=args['per_page'])
        return Response(result, PromoCodeListResponse).create(), 200

    @jwt_only
    @admin_only
    @jsoned
    def get_one(self, promocode_id):
        result = self.promocodes.get_one(promocode_id)
        return PromoCodeResponse.create(result), 200

    @jwt_only
    @admin_only
    @jsoned
    def get_products(self):
        result = self.products.promocode_products()
        return ProductDetailResponse.create(result), 200

    @jwt_only
    @admin_only
    @jsoned
    def create(self):     
        data = request.get_json()
        quantity = data.pop('quantity', 1)
        result = self.promocodes.create(data, quantity=quantity, creator=self.current_user )
        return PromoCodeResponse.create(result), 200
    
    
    @jwt_only
    @admin_only
    @jsoned
    def remove(self, promocode_id):
        promocode = self.promocodes.get_one(promocode_id) or abort(404)
        self.promocodes.remove(promocode)
        return {}, 200

