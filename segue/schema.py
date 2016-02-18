# -*- coding: utf-8 -*-

from marshmallow import fields, schema, validate

from segue.babel import _l
from segue.core import ma
from segue.core import config


class BaseSchema(ma.Schema):

    class Meta:
        dateformat="%d/%m/%Y"

class Field(object):
    """A factory for create marshmallow fields with internationalization messages"""

    DEFAULT_MSGS = {
        'required': _l('Missing data for required field.'),
        'type': _l('Invalid input type.'),
        'null': _l('Field may not be null.'),
        'validator_failed': _l('Invalid value.')
    }

    CLS_MSGS = {
        'Integer': {
            'invalid': _l('Not a valid integer.')
        },
        'String': {
            'invalid': _l('Not a valid string.')
        },
        'Boolean': {
            'invalid': _l('Not a valid boolean.'),
        },
        'Date': {
            'invalid': _l('Not a valid date.'),
            'format': _l('"{input}" cannot be formatted as a date.'),
        }
    }

    @staticmethod
    def str(*args, **kwargs):
        return Field.create(fields.String, *args, **kwargs)

    @staticmethod
    def int(*args, **kwargs):
        return Field.create(fields.Integer, *args, **kwargs)

    @staticmethod
    def date(*args, **kwargs):
        return Field.create(fields.Date, *args, **kwargs)

    @staticmethod
    def bool(*args, **kwargs):
        return Field.create(fields.Boolean, *args, **kwargs)

    @staticmethod
    def create(cls, *args, **kwargs):

        msgs = Field.DEFAULT_MSGS.copy()
        msgs.update(Field.CLS_MSGS.get(cls.__name__, {}))
        msgs.update(kwargs.get('error_messages', {}))
        kwargs['error_messages'] = msgs

        return cls(*args, **kwargs)


class Validator(object):

    MSGS = {
        'oneOf': _l('Not a valid choice.'),
        'email': _l('Not a valid email address.'),
        'length_min': _l('Shorter than minimum length {min}.'),
        'length_max': _l('Longer than maximum length {max}.'),
        'length_all': _l('Length must be between {min} and {max}.'),
        'length_equal': _l('Length must be {equal}.')
    }

    @staticmethod
    def email():
        return validate.Email(error=Validator.MSGS['email'])

    @staticmethod
    def length(min=None, max=None, equal=None):
        error = None
        if equal:
            error = Validator.MSGS['length_equal']
        elif min and max:
            error = Validator.MSGS['length_all']
        elif min:
            error = Validator.MSGS['length_min']
        elif max:
            error = Validator.MSGS['length_max']
        return validate.Length(min=min, max=max, equal=equal, error=error)

    @staticmethod
    def one_of(choices=None):
        return validate.OneOf(choices, error=Validator.MSGS['oneOf'])