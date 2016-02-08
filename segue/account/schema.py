import copy

ACCOUNT_ROLES = [ "user","operator","admin","employee","cashier", "coporate"]
CPF_PATTERN = "^\d{3}.?\d{3}.?\d{3}-?\d{2}$"
NAME_PATTERN = r"(.*)\s(.*)"
DISABILITY_TYPES = ["none","hearing","mental","physical","visual"]

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
