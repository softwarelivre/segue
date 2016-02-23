import copy
from marshmallow import validates_schema, validates


from errors import EmailAddressMisMatch, PasswordsMisMatch, InvalidCNPJ, InvalidCPF
from segue.schema import BaseSchema, Field, Validator
from segue.validation import CPFValidator
from segue.validation import CNPJValidator


ACCOUNT_ROLES = [ "user","operator","admin","employee","cashier", "coporate"]
CPF_PATTERN = "^\d{3}.?\d{3}.?\d{3}-?\d{2}$"
NAME_PATTERN = r"(.*)\s(.*)"
DISABILITY_TYPES = ["none","hearing","mental","physical","visual"]


class AccountSchema(BaseSchema):

        id = Field.int(dump_only=True)
        email = Field.str(
            required=True,
            validate=[Validator.length(min=5, max=40), Validator.email()]
        )
        email_confirm = Field.str(
            required=True,
            validate=[Validator.length(min=5, max=40), Validator.email()]
        )
        name = Field.str(
            required=True,
            validate=[Validator.length(min=5, max=40)]
        )
        badge_name = Field.str()
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
        passport = Field.str(
            validate=[Validator.length(min=5, max=20)]
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
            if 'password' or 'password_confirm' in data:
                if data.get('password', None) != data.get('password_confirm', None):
                    raise PasswordsMisMatch()

            if 'email' in data and 'email_confirm' in data:
                if data.get['email'] != data.get['email_confirm']:
                    raise EmailAddressMisMatch()


class CreateAccountSchema(AccountSchema):
    pass


class AdminCreateAccount(AccountSchema):

    def __init__(self, *args, **kwargs):
        super(AdminCreateAccount, self).__init__(*args, **kwargs)
        del self.fields['email_confirm']

class AdminEditAccount(AccountSchema):

    def __init__(self, *args, **kwargs):
        super(AdminEditAccount, self).__init__(*args, **kwargs)
        self.fields['password'].required = False
        del self.fields['password_confirm']
        del self.fields['email']
        del self.fields['email_confirm']

signup = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "email":        { "type": "string", "minLength": 5,  "maxLength": 80, "format": "email" },
	"email_confirm":{ "type": "string", "minLength": 5,  "maxLength": 80, "format": "email" },
        "name":         { "type": "string", "minLength": 5,  "maxLength": 80, "pattern": NAME_PATTERN},
        "badge_name":         { "type": "string",  "maxLength": 80},
        "password":     { "type": "string", "minLength": 5,  "maxLength": 80 },
        "password_confirm":     { "type": "string", "minLength": 5,  "maxLength": 80 },
        "disability":   { "type": "string", "enum": DISABILITY_TYPES },
        "disability_info": { "type": "string", "maxLength": 200},
        "document":     { "type": "string", "minLength": 5,  "maxLength": 15 },
	    "student_document":   { "type": "string", "maxLength": 30},
        "phone":        { "type": "string", "minLength": 5,  "maxLength": 30 },
        "organization": { "type": "string", "maxLength": 80 },
        "resume":       { "type": "string",  "maxLength": 400 },
        "occupation":      { "type": "string", "minLength": 1,  "maxLength": 20  },
        "education":       { "type": "string", "minLength": 1,  "maxLength": 40  },
        "sex":             { "type": "string", "minLength": 1,  "maxLength": 1  },
        "born_date":       { "type": "string", "minLength": 10, "maxLength": 10 },
	    "membership":      { "type": "boolean"},
        "country":      { "type": "string", "minLength":1,  "maxLength": 20 },
        "city":         { "type": "string", "minLength": 3,  "maxLength": 30 },
        "address_street":  { "type": "string", "minLength": 5,  "maxLength": 80  },
        "address_number":  { "type": "string", "minLength": 1,  "maxLength": 20  },
        "address_extra":   { "type": "string", "minLength": 0,  "maxLength": 40  },
        "address_state":   { "type": "string", "minLength": 2,  "maxLength": 2  },
        "address_neighborhood": { "type": "string", "minLength": 2,  "maxLength": 20  },
        "address_zipcode": { "type": "string", "minLength": 2,  "maxLength": 9  },
    },
    "required": [
        "email", "name", "password", "document", "country", "city", "phone",
        "address_street", "address_number", "address_state", "address_neighborhood",
        "address_zipcode", "occupation", "education", "sex", "born_date","membership"
    ],
}
edit_account = copy.deepcopy(signup)
edit_account['required'].remove('password')

corporate = copy.deepcopy(signup)
corporate['required'].remove('occupation')
corporate['required'].remove('education')
corporate['required'].remove('sex')
corporate['required'].remove('born_date')
corporate['required'].remove('membership')

del corporate['properties']['occupation']
del corporate['properties']['education']
del corporate['properties']['sex']
del corporate['properties']['born_date']
del corporate['properties']['membership']

edit_corporate = copy.deepcopy(corporate)
edit_corporate['required'].remove('password')

reset = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "hash_code": { "type": "string", "minLength": 5,  "maxLength": 64 },
        "password":  { "type": "string", "minLength": 8,  "maxLength": 80 },
    },
    "required": ["hash_code", "password" ],
}

admin_create = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "email":        { "type": "string", "minLength": 5, "maxLength": 80, "format": "email" },
        "name":         { "type": "string", "minLength": 5, "maxLength": 80 },
        "document":     { "type": "string", "minLength": 5, "maxLength": 14 },
        "country":      { "type": "string", "minLength": 5, "maxLength": 30 },
    },
    "required": ["email", "name", "country", "document" ],
}
admin_edit = admin_create.copy()

whitelist = dict(
  signup=signup,
  corporate=corporate,
  edit_account=edit_account,
  edit_corporate=edit_corporate,
  reset=reset,
  admin_create=admin_create,
  admin_edit=admin_edit
)
