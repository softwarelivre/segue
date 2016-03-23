from segue.schema import BaseSchema, Field, Validator

class CaravanSchema(BaseSchema):
    id = Field.int(dump_only=True)
    name = Field.str(
        required=True,
        validate=[Validator.length(min=5, max=80)]
    )
    city = Field.str(
        required=True,
        validate=[Validator.length(min=5, max=80)]
    )
    description = Field.str(
        required=True,
        validate=[Validator.length(min=5, max=400)]
    )

class CaravanInvite(BaseSchema):
    id = Field.int(dump_only=True)
    name = Field.str(
        required=True,
        validate=[Validator.length(min=5, max=80)]
    )
    recipient = Field.str(
        required=True,
        validate=[Validator.length(min=5, max=60), Validator.email()]
    )

new_caravan = CaravanSchema()
edit_caravan = CaravanSchema()
new_invite = CaravanInvite()


whitelist = dict(
    new_caravan=new_caravan,
    edit_caravan=edit_caravan,
    new_invite=new_invite
)
