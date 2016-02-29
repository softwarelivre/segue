import re
from marshmallow import validates_schema, validates

from errors import InvalidCNPJ, InvalidCPF, InvalidZipCodeNumber
from segue.schema import BaseSchema, Field, Validator
from segue.validation import CPFValidator, CNPJValidator, ZipCodeValidator


BUYER_TYPES = ['person','company','government']

class BuyerSchema(BaseSchema):

    kind = Field.str(
        required=True,
        validate=[Validator.one_of(choices=BUYER_TYPES)]
    )
    name = Field.str(
        required=True,
        validate=[Validator.length(min=5, max=80)]
    )
    contact = Field.str(
        required=True,
        validate=[Validator.length(min=5, max=30)]
    )
    cpf = Field.str()
    cnpj = Field.str()
    passport = Field.str()
    document = Field.str(dump_only=True)

    address_country = Field.str(
        required=True,
        validate=[Validator.length(min=3, max=20)]
    )
    address_city = Field.str(
        required=True,
        validate=[Validator.length(min=3, max=30)]
    )
    address_street = Field.str(
        required=True,
        validate=[Validator.length(min=5, max=80)]
    )
    address_number = Field.str(
        required=True,
        validate=[Validator.length(min=1, max=20)]
    )
    address_extra = Field.str(
        validate=[Validator.length(max=40)]
    )
    address_state = Field.str(
        required=True,
        validate=[Validator.length(equal=2)]
    )
    address_neighborhood = Field.str(
        required=True,
        validate=[Validator.length(min=3, max=30)]
    )
    address_zipcode = Field.str(
        required=True,
        validate=[Validator.length(min=3, max=15)]
    )

    @validates('cpf')
    def validate_cpf(self, data):
        if not CPFValidator(data).is_valid():
            raise InvalidCPF()

    @validates('cnpj')
    def validate_cnpj(self, data):
        if not CNPJValidator(data).is_valid():
            raise InvalidCNPJ()

    @validates_schema()
    def validate(self, data):
        #TODO: IMPROVE
        if re.match(r'br.*', data.get('country', ''), re.IGNORECASE):
            if not ZipCodeValidator(data.get('address_zipcode', None)).is_valid():
                raise InvalidZipCodeNumber()

buyer = BuyerSchema()
promocode = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "hash_code": { "type": "string", "minLength": 12, "maxLength": 12 }
    },
    "required": [
        "hash_code"
    ]
}
create_promocode = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "description": { "type": "string",  "minLength": 5, "maxLength": 50 },
        "quantity":    { "type": "integer", "minimum":   1, "maximum":   100 },
        "discount":    { "type": "integer", "minimum":   0, "maximum":   100 },
        "product_id":  { "type": "integer" }
    },
    "required": [
        "description", "product_id"
    ]
}

whitelist = dict(
    buyer = buyer,
    promocode = promocode,
    create_promocode = create_promocode
)
