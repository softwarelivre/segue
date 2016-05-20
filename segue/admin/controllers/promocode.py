from flask import request, abort
from flask.ext.jwt import current_user

from segue.core import cache, config
from segue.decorators import jsoned, jwt_only, admin_only

from segue.purchase.promocode import PromoCodeService
from segue.product.services import ProductService
from segue.errors import SchemaValidationError


from ..responses import PromoCodeResponse, ProductDetailResponse

class AdminPromoCodeController(object):
    def __init__(self, promocodes=None, products=None):
        self.current_user = current_user
        self.promocodes   = promocodes or PromoCodeService()
        self.products     = products   or ProductService()

    @jwt_only
    @admin_only
    @jsoned
    def list_promocodes(self):
        parms = request.args.to_dict()
        result = self.promocodes.lookup(as_user=self.current_user, **parms)
        return PromoCodeResponse.create(result), 200

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
        if not self.current_user.id in config.CAN_CREATE_PROMOCODE:
            abort(400)

        from segue.purchase.promocode.factories import PromoCodeFactory
        from segue.purchase.schema import PromoCodeSchema

        data = request.get_json()

        parsed_data, errors = PromoCodeSchema().load(data)
        if errors:
            raise SchemaValidationError(errors)

        product_id = parsed_data.pop('product_id')
        description = parsed_data.pop('description')
        quantity = parsed_data.pop('quantity')

        product = self.products.get_product(product_id, strict=True) or abort(404)

        result = self.promocodes.create(product, creator=self.current_user, quantity=quantity, description=description)

        return PromoCodeResponse.create(result), 200
