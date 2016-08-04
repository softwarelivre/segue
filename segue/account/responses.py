from segue.schema import Field
from schema import AccountSchema, RoleSchema


class AccountResponse(AccountSchema):

    #TODO: REMOVE ROLE
    role = Field.str()
    roles = Field.nested(RoleSchema, many=True)

    has_valid_purchases = Field.bool()
    #TODO REMOVE THIS HACK
    incharge = Field.str()

    certificate_name = Field.str()

    class Meta:
        exclude = ('password',)

class EmployeesListResponse(AccountSchema):

    purchase_id = Field.str(attribute='purchase.id')
    name = Field.str(attribute='purchase.customer.name')
    document = Field.str(attribute='purchase.customer.document')
    hash_code = Field.str(attribute='promocode.hash_code')
