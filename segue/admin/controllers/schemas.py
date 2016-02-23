from segue.schema import Field, BaseSchema
from segue.account.schema import AccountSchema
from marshmallow import fields

class PurchasePersonIdentifier(BaseSchema):
    id = Field.int()
    name = Field.str(attribute='customer.name')
    status = Field.str()
    category = Field.str(attribute='product.category')


class AccountDetail(AccountSchema):

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

