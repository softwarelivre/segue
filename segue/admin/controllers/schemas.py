from segue.schema import Field, BaseSchema
from segue.account.schema import AccountSchema, RoleSchema
from segue.purchase.schema import BuyerSchema
from segue.product.schema import ProductSchema
from marshmallow import fields

class PurchasePersonIdentifier(BaseSchema):
    id = Field.int()
    name = Field.str(attribute='customer.name')
    status = Field.str()
    category = Field.str(attribute='product.category')


class AccountDetail(AccountSchema):

    roles = fields.Nested(RoleSchema, many=True)
    has_valid_purchases = Field.bool()
    identifier = fields.Nested(PurchasePersonIdentifier, attribute='identifier_purchase')

    links = Field.links({
        'proposals': {
            'href': Field.url('admin.account.proposals_of_account', account_id='<id>')
        },
        'purchases': {
            'href': Field.url('admin.list_purchases', customer_id='<id>'),
        },
        'payments': {
            'href': Field.url('admin.list_payments', customer_id='<id>'),
        },
        'caravans': {
            'href': Field.url('admin.list_caravans', owner_id='<id>')
        }
    })

    class Meta:
        exclude = ('password',)

#TODO: REVIEW
class PurchaseDetail(BaseSchema):
    id = Field.int()
    kind = Field.str()
    category = Field.str()
    public = Field.str()
    price = Field.decimal()
    sold_until = Field.date()
    status = Field.str()
    description = Field.str()
    created = Field.date()

    buyer = fields.Nested(BuyerSchema)
    product = fields.Nested(ProductSchema)

    #TODO: FIX
    customer_id = Field.int(attribute='customer.id')
    customer_name = Field.str(attribute='customer.name')

    links = Field.links({
        'customer': {
            'href': Field.url('admin.account.get_one', account_id='<id>')
        },
        'payments': {
            'href': Field.url('admin.list_payments', purchase_id='<id>')
        }
    })
