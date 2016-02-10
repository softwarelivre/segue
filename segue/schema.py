# -*- coding: utf-8 -*-

from marshmallow import fields, schema, validate
from flask.ext.babelex import lazy_gettext
from segue.core import ma


class BaseSchema(ma.Schema):
    pass


class Field(object):
    """A factory for create marshmallow fields with internationalization messages"""

    DEFAULT_MSGS = {
        'required': lazy_gettext('Missing data for required field.'),
        'type': lazy_gettext('Invalid input type.'),
        'null': lazy_gettext('Field may not be null.'),
        'validator_failed': lazy_gettext('Invalid value.')
    }

    CLS_MSGS = {
        'Integer': {
            'invalid': lazy_gettext('Not a valid integer.')
        },
        'String': {
            'invalid': lazy_gettext('Not a valid string.')
        }
    }

    @staticmethod
    def str(*args, **kwargs):
        return Field.create(fields.String, *args, **kwargs)

    @staticmethod
    def int(*args, **kwargs):
        return Field.create(fields.Integer, *args, **kwargs)

    @staticmethod
    def create(cls, *args, **kwargs):

        msgs = Field.DEFAULT_MSGS.copy()
        msgs.update(Field.CLS_MSGS.get(cls.__name__, {}))
        msgs.update(kwargs.get('error_messages', {}))
        kwargs['error_messages'] = msgs

        return cls(*args, **kwargs)


#class Validator(object):
#
#    @staticmethod
#    def OneOf(*args, **kwargs):
#        pass
#
#    @staticmethod
#    def create(cls, *args, **kwargs):
#        return cls(min=4, error=gettext('Must be at least {min}.'))