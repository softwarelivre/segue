ACCOUNT_ROLES = [ "user","operator","admin","employee","cashier"]
CPF_PATTERN = "^\d{3}.?\d{3}.?\d{3}-?\d{2}$"
NAME_PATTERN = r"(.*)\s(.*)"

signup = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "email":        { "type": "string", "minLength": 5,  "maxLength": 80, "format": "email" },
        "name":         { "type": "string", "minLength": 5,  "maxLength": 80, "pattern": NAME_PATTERN},
        "password":     { "type": "string", "minLength": 5,  "maxLength": 80 },
        "cpf":          { "type": "string", "minLength": 11, "maxLength": 14, "pattern": CPF_PATTERN },
        "document":     { "type": "string", "minLength": 5,  "maxLength": 14 },
        "passport":     { "type": "string", "minLength": 5,  "maxLength": 15 },
        "country":      { "type": "string", "minLength": 5,  "maxLength": 30 },
        "city":         { "type": "string", "minLength": 3,  "maxLength": 30 },
        "phone":        { "type": "string", "minLength": 5,  "maxLength": 30 },
        "organization": { "type": "string", "minLength": 3,  "maxLength": 80 },
        "resume":       { "type": "string", "minLength": 5,  "maxLength": 400 },
    },
    "required": ["email", "name", "password", "country", "city", "phone" ],
}
edit_account = signup.copy()
edit_account['required'] = ["email", "name", "country", "city", "phone" ]

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
  edit_account=edit_account,
  reset=reset,
  admin_create=admin_create,
  admin_edit=admin_edit
)
