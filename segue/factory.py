import jsonschema

from segue.core import logger
from segue.schema import BaseSchema

from errors import SegueValidationError, SchemaValidationError

class Factory(object):
    @classmethod
    def clean_for_insert(cls, data):
        return data

    @classmethod
    def clean_for_update(cls, data):
        return data

    @classmethod
    def parse(cls, data, schema):
        parsed_data, errors = schema.load(data)
        if errors:
            raise SchemaValidationError(errors)
        return parsed_data

    @classmethod
    def update_model(cls, model, data, schema):
        if isinstance(model, cls.model):
            parsed_data = cls.parse(data, schema)
            for name, value in cls.clean_for_update(parsed_data).items():
                setattr(model, name, value)
            return model

    @classmethod
    def from_json(cls, data, schema):
        data.pop('$type', None)
        # TODO: REMOVE LATER
        if isinstance(schema, BaseSchema):
            parsed_data = cls.parse(data, schema)
            cleaned_data = cls.clean_for_insert(parsed_data)
            return cls.model(**cleaned_data)
        else:
            validator = jsonschema.Draft4Validator(schema, format_checker=jsonschema.FormatChecker())
            errors = list(validator.iter_errors(data))
            cleaned_data = cls.clean_for_insert(data)
            if errors:
                logger.error('validation error for %s.from_json: %s', cls, errors)
                raise SegueValidationError(errors)
            return cls.model(**cleaned_data)


