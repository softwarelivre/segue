ACCOUNT_ROLES = [ "user","operator","admin","employee" ]
CPF_PATTERN = "^\d{3}.?\d{3}.?\d{3}-?\d{2}$"

signup = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "email":        { "type": "string", "minLength": 5,  "maxLength": 80, "format": "email" },
        "name":         { "type": "string", "minLength": 5,  "maxLength": 80 },
        "password":     { "type": "string", "minLength": 5,  "maxLength": 80 },
        "cpf":          { "type": "string", "minLength": 11, "maxLength": 14, "pattern": CPF_PATTERN },
        "passport":     { "type": "string", "minLength": 5,  "maxLength": 15 },
        "country":      { "type": "string", "minLength": 5,  "maxLength": 30 },
        "city":         { "type": "string", "minLength": 2,  "maxLength": 60 },
        "phone":        { "type": "string", "minLength": 5,  "maxLength": 30 },
        "organization": { "type": "string", "minLength": 5,  "maxLength": 30 },
        "resume":       { "type": "string", "minLength": 5,  "maxLength": 400 },
        "role":         { "enum": ACCOUNT_ROLES }
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

whitelist = dict(
  signup=signup,
  edit_account=edit_account,
  reset=reset
)
