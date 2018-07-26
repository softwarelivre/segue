from marshmallow import validates_schema, validates

from segue.schema import BaseSchema, Field, Validator
from segue.errors import FieldError

PROPOSAL_LEVELS = ['beginner', 'advanced']
PROPOSAL_TYPES = ['talk', 'workshop']
ACCEPTED_LANGUAGES = ['pt', 'en', 'es']


class ProposalSchema(BaseSchema):
    title = Field.str(
        required=True,
        validate=[Validator.length(min=5, max=85)]
    )
    full = Field.str(
        required=True,
        validate=[Validator.length(min=5, max=2000)]
    )
    language = Field.str(
        required=True,
        validate=[Validator.one_of(ACCEPTED_LANGUAGES)]
    )
    level = Field.str(
        required=True,
        validate=[Validator.one_of(PROPOSAL_LEVELS)]
    )
    type = Field.str(
        required=True,
        validate=[Validator.one_of(PROPOSAL_TYPES)]
    )
    restrictions = Field.str(
        validate=[Validator.length(max=500)]
    )
    expected_duration = Field.decimal()
    demands = Field.str(
        validate=[Validator.length(max=500)]
    )
    track_id = Field.int(required=True)

    @validates_schema
    def validate(self, data):
        if 'type' in data and data['type'] == 'workshop':
            if 'expected_duration' not in data:
                #TODO: CREATE AN EXCEPTION
                raise FieldError(Field.DEFAULT_MSGS['required'], 'expected_duration')



class AdminProposalSchema(ProposalSchema):
    owner_id = Field.int(required=True)


class InviteSchema(BaseSchema):
    recipient = Field.str(
        required=True,
        validate=[Validator.length(min=5, max=40), Validator.email()]
    )
    name = Field.str(
        required=True,
        validate=[Validator.length(min=5, max=40)]
    )


new_proposal = ProposalSchema()
edit_proposal = ProposalSchema()
admin_proposal = AdminProposalSchema()

new_invite = InviteSchema()

#TODO: REMOVE
old_new_proposal = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "title":    { "type": "string", "minLength": 5, "maxLength": 80   },
        "full":     { "type": "string", "minLength": 5, "maxLength": 2000 },
        "language": { "type": "string", "minLength": 2, "maxLenght": 2 },
        "level":    { "enum": PROPOSAL_LEVELS },
        "track_id": { "type": "integer" },
    },
    "required": [ "title", "full", "language", "level" ]
}
#TODO: REMOVE
old_edit_proposal = old_new_proposal.copy()

#TODO: REMOVE
old_new_invite = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "recipient": { "type": "string", "minLength": 5, "maxLength": 80, "format": "email" },
        "name":      { "type": "string", "minLength": 5, "maxLength": 80 },
    },
    "required": [ "recipient", "name" ]
}

#TODO: REMOVE
old_admin_create = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "title":     { "type": "string", "minLength": 5, "maxLength": 80   },
        "full":      { "type": "string", "minLength": 5, "maxLength": 2000 },
        "language":  { "type": "string", "minLength": 2, "maxLenght": 2 },
        "level":     { "enum": PROPOSAL_LEVELS },
        "track_id":  { "type": "integer" },
        "owner_id ": { "type": "integer" },
    },
    "required": [ "title", "full", "language", "level", "owner_id", "track_id" ]
    }

whitelist = dict(
    new_proposal  = old_new_proposal,
    edit_proposal = old_edit_proposal,
    new_invite    = old_new_invite,
    admin_create  = old_admin_create
)
