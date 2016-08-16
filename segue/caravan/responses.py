from segue.schema import Field, BaseSchema



from schema import CaravanSchema

from segue.account.schema import AccountSchema

class CaravanResponse(CaravanSchema):
    owner = Field.nested(AccountSchema, only=['id','name'])


class CaravanListResponse(BaseSchema):

    id   = Field.int()
    name = Field.str()
    city = Field.str()
    owner = Field.nested(AccountSchema, only=['id','name'])


class CaravanInviteResponse(BaseSchema):

    id = Field.int()
    name = Field.str()
    recipient = Field.str()
    hash = Field.str()
    status = Field.str()