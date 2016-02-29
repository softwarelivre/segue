from segue.schema import Field
from schema import AccountSchema

class AccountResponse(AccountSchema):

    has_valid_purchases = Field.bool()

    class Meta:
        exclude = ('password',)