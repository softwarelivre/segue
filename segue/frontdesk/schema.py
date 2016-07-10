# -*- coding: utf-8 -*-

import re
from marshmallow import validates_schema, validates

from segue.errors import FieldError
from segue.schema import BaseSchema, Field, Validator
from segue.validation import CPFValidator, CNPJValidator, ZipCodeValidator

from segue.account.errors import InvalidCNPJ, InvalidCPF, InvalidZipCodeNumber

create = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "email":        { "type": "string", "minLength": 5,  "maxLength": 80, "format": "email" },
    },
    "required": [ 'email'  ]
}

patch = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "email":        { "type": "string", "minLength": 5,  "maxLength": 80, "format": "email" },
        "name":         { "type": "string", "minLength": 5,  "maxLength": 80 },
        "password":     { "type": "string", "minLength": 5,  "maxLength": 80 },
        "document":     { "type": "string", "minLength": 5,  "maxLength": 14 },
        "passport":     { "type": "string", "minLength": 5,  "maxLength": 15 },
        "country":      { "type": "string", "minLength": 5,  "maxLength": 30 },
        "city":         { "type": "string", "minLength": 3,  "maxLength": 30 },
        "phone":        { "type": "string", "minLength": 5,  "maxLength": 30 },
        "organization": { "type": "string", "minLength": 3,  "maxLength": 30 },
        "resume":       { "type": "string", "minLength": 5,  "maxLength": 400 },
    },
    "required": [ ]
}

whitelist=dict(
    patch=patch,
    create=create,
)

class VisitorSchema(BaseSchema):
    name = Field.str(
        required=True,
        validate=[Validator.length(min=5, max=80)]
    )

    badge_name = Field.str(
        validate=[Validator.length(max=20)]
    )

    email = Field.str(
        required=True,
        validate=[Validator.length(min=5, max=60), Validator.email()]
    )

    document = Field.str(
        required=True
    )

    phone = Field.str(
        required=True
    )

    @validates('document')
    def validate_cpf(self, data):
        if not CPFValidator(data).is_valid():
            raise InvalidCPF()


class PeopleSchema(BaseSchema):

        id = Field.int(dump_only=True)
        role = Field.str(dump_only=True)
        #TODO: REMOVE THIS HACK
        type = Field.str()
        # TODO: REMOVE THIS HACK
        incharge = Field.str()

        email = Field.str(
            required=True,
            validate=[Validator.length(min=5, max=60), Validator.email()]
        )

        name = Field.str(
            required=True,
            validate=[Validator.length(min=5, max=80)]
        )

        phone = Field.str(
            required=True
        )

        cpf = Field.str()
        cnpj = Field.str()
        passport = Field.str()
        document = Field.str(dump_only=True)

        resume = Field.str()

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

            #TODO: FIX THIS HACKSSS
            if 'type' in data:
                if data['type'] == 'corporate':
                    incharge = data.get('incharge', '')
                    if len(incharge.strip()) == 0:
                        raise FieldError(message=u'Por favor, digite o nome do responsável', field='incharge')
                elif not re.match(r'.*\ .*', data.get('name', ''), re.IGNORECASE):
                    raise FieldError(message=u'Por favor, digite seu nome e sobre nome', field='name')

            #TODO: IMPROVE
            if re.match(r'br.*', data.get('country', ''), re.IGNORECASE):
                if not ZipCodeValidator(data.get('address_zipcode', None)).is_valid():
                    raise InvalidZipCodeNumber()



class PeopleAddressSchema(BaseSchema):

    country = Field.str(
        required=True,
        validate=[Validator.length(min=3, max=20)]
    )

    address_state = Field.str(
        required=True,
        validate=[Validator.length(min=3, max=20)]
    )

    city = Field.str(
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

    @validates_schema()
    def validate(self, data):
        # TODO: IMPROVE
        if re.match(r'br.*', data.get('country', ''), re.IGNORECASE):
            if not ZipCodeValidator(data.get('address_zipcode', None)).is_valid():
                raise InvalidZipCodeNumber()


class BadgeSchema(BaseSchema):

    badge_name = Field.str(
        validate=[Validator.length(max=20)]
    )

    badge_corp = Field.str(
        validate=[Validator.length(max=20)]
    )

create_people = PeopleSchema()