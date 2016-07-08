# -*- coding: utf-8 -*-

import re
from marshmallow import validates_schema, validates


from errors import EmailAddressMisMatch, PasswordsMisMatch, InvalidCNPJ, InvalidCPF, InvalidZipCodeNumber
from segue.errors import FieldError
from segue.schema import BaseSchema, Field, Validator
from segue.validation import CPFValidator, CNPJValidator, ZipCodeValidator


ACCOUNT_ROLES = [ "user","operator","admin","employee","cashier", "corporate", "foreign"]
CPF_PATTERN = "^\d{3}.?\d{3}.?\d{3}-?\d{2}$"
NAME_PATTERN = r"(.*)\s(.*)"
DISABILITY_TYPES = ["none","hearing","mental","physical","visual"]


class AccountSchema(BaseSchema):

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
        email_confirm = Field.str(
            required=True,
            validate=[Validator.length(min=5, max=60), Validator.email()]
        )
        name = Field.str(
            required=True,
            validate=[Validator.length(min=5, max=80)]
        )
        badge_name = Field.str(
            validate=[Validator.length(max=20)]
        )
        password = Field.str(
            required=True,
            validate=[Validator.length(min=8, max=20)]
        )
        password_confirm = Field.str(
            required=True,
            validate=[Validator.length(min=8, max=20)]
        )
        disability = Field.str(
            validate=[Validator.one_of(choices=DISABILITY_TYPES)]
        )
        disability_info = Field.str(
            validate=[Validator.length(max=400)]
        )

        cpf = Field.str()
        cnpj = Field.str()
        passport = Field.str()
        document = Field.str(dump_only=True)

        student_document = Field.str()
        phone = Field.str(
            required=True,
            validate=[Validator.length(min=5, max=30)]
        )
        organization = Field.str()
        resume = Field.str(
            validate=[Validator.length(max=400)]
        )
        occupation = Field.str(
            required=True,
            validate=[Validator.length(min=1, max=20)]
        )

        occupation_position       = Field.str()
        occupation_decision_power = Field.str()
        employer_activity         = Field.str()
        employer_size             = Field.str()

        education = Field.str(
            required=True,
            validate=[Validator.length(min=1, max=40)]
        )
        sex = Field.str(
            required=True,
            validate=[Validator.length(equal=1)]
        )
        born_date = Field.date(required=True)
        membership = Field.bool(required=True)

        inform = Field.bool(required=True)

        country = Field.str(
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

        caravan_invite_hash = Field.str(dump=True, attribute='caravan_invite_hash')

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
                    print data
                    incharge = data.get('incharge', '')
                    if len(incharge.strip()) == 0:
                        raise FieldError(message=u'Por favor, digite o nome do responsável', field='incharge')
                elif not re.match(r'.*\ .*', data.get('name', ''), re.IGNORECASE):
                    raise FieldError(message=u'Por favor, digite seu nome e sobre nome', field='name')

            if 'password' or 'password_confirm' in data:
                if data.get('password', None) != data.get('password_confirm', None):
                    raise PasswordsMisMatch()

            if 'email' in data and 'email_confirm' in data:
                if data.get('email') != data.get('email_confirm'):
                    raise EmailAddressMisMatch()

            #TODO: IMPROVE
            if re.match(r'br.*', data.get('country', ''), re.IGNORECASE):
                if not ZipCodeValidator(data.get('address_zipcode', None)).is_valid():
                    raise InvalidZipCodeNumber()

class CreateAccountSchema(AccountSchema):
    pass


class EditAccountSchema(AccountSchema):
    def __init__(self, *args, **kwargs):
        super(EditAccountSchema, self).__init__(*args, **kwargs)
        self.fields['password'].required = False
        self.fields['password_confirm'].required = False
        del self.fields['email']
        del self.fields['email_confirm']


class AccountTokenSchema(BaseSchema):
    type = Field.str(dump_only=True, default='Account.token')

    def serialize(self, account):
        return self.dump(account).data

    class Meta:
        fields = ('id', 'name', 'email', 'role', 'roles', 'dirty')

#TODO: CREATE A SCHEMA
reset = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "hash_code": { "type": "string", "minLength": 5,  "maxLength": 64 },
        "password":  { "type": "string", "minLength": 8,  "maxLength": 80 },
    },
    "required": ["hash_code", "password" ],
}

exclude_from_corporate = ['occupation', 'education', 'sex', 'born_date', 'membership']

whitelist = dict(
  create_corporate=CreateAccountSchema(exclude=exclude_from_corporate),
  edit_corporate=EditAccountSchema(exclude=exclude_from_corporate),
  create_account=CreateAccountSchema(),
  edit_account=EditAccountSchema(),
  reset=reset
)
