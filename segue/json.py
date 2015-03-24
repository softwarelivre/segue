from werkzeug.wrappers import Response
from functools import wraps
import flask
import decimal
import datetime

import core

def accepts_html(f):
    @wraps(f)
    def wrapper(*args, **kw):
        best = flask.request.accept_mimetypes.best_match(['application/json', 'text/html'])
        kw['wants_html'] = best == 'text/html'
        return f(*args, **kw)
    return wrapper

def jsoned(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        status = 200
        result = f(*args, **kwargs)
        if isinstance(result, Response):
            return result
        if isinstance(result, tuple):
            result, status = result
        if isinstance(result, list):
            return flask.jsonify(dict(items=result)), status
        elif isinstance(result, dict):
            return flask.jsonify(dict(**result)), status
        elif hasattr(result, 'to_json'):
            return flask.jsonify(dict(resource=result.to_json())), status
        else:
            return flask.jsonify(dict(resource=result)), status
    return wrapper


class JSONEncoder(flask.json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return "{0:0.2f}".format(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        if isinstance(obj, JsonSerializable):
            return obj.serialize()
        return super(JSONEncoder, self).default(obj)

class JsonSerializable(object):
    _serializers = [ ]

    def serialize(self, **kw):
        instance_using = getattr(self, '_using', None)
        argument_using = kw.pop('using',None)
        first_option = argument_using or instance_using or None
        candidates = [ first_option ] if first_option else []
        candidates.extend(self._serializers)
        candidates.append(JsonSerializer)
        serializer = candidates[0]()
        return serializer.emit_json_for(self, **kw)

    def serializing_with(self, impl):
        self._using = constantize(self._serializers, impl).__class__
        return self

    def to_json(self, **kw):
        return self.serialize(**kw)

class JsonSerializer(object):
    _serializer_name = 'default'

    def __init__(self, **overrides):
        self.debug_mode = core.config.DEBUG or False
        self.serializer_overrides = overrides

    def hide_field(self, child):
        return False;

    def serialize_child(self, child):
        return False

    def emit_json_for(self, target, **kw):
        if hasattr(target, 'to_json'):
            return target.to_json()
        return target

class JsonFor(object):
    def __init__(self, target):
        self.target = target

    def using(self, serializer_name):
        for item in list(self.target):
            item.serializing_with(serializer_name)
        return self.target

def constantize(glossary, selected):
    for cls in glossary:
        if cls.__name__ == selected:
            return cls()


class PropertyJsonSerializer(JsonSerializer):
    _serializer_name = 'properties'
    def get_field_names(self, target):
        raise NotImplementedError()

    def emit_json_for(self, target, **overrides):
        # WORST CODE EVER
        overrides.update(self.serializer_overrides)
        result = {}
        for key, serializer in self.get_field_names(target):
            value          = getattr(target, key, None)
            override       = overrides.get(key, None)
            hide_field     = self.hide_field(key)
            recurse_with   = self.serialize_child(key)
            is_list        = isinstance(value, list)
            is_nested_list = is_list and any([ isinstance(x, JsonSerializable) for x in value ])
            is_nested      = is_nested_list or isinstance(value, JsonSerializable)
            is_lazy_rel    = hasattr(value, "all")
            available      = value[0]._serializers if is_nested_list else getattr(value, '_serializers', [])

            selected   = override or recurse_with or 'JsonSerializer'
            serializer = constantize(available, selected) or JsonSerializer()
            if is_nested_list:
                if not recurse_with: continue
                result[key] = [ serializer.emit_json_for(item, **overrides) for item in value ]
            elif is_nested:
                if not recurse_with: continue
                result[key] = serializer.emit_json_for(value, **overrides)
            elif is_lazy_rel:
                if not recurse_with: continue
                result[key] = serializer.emit_json_for(value.all(), **overrides)
            elif value and not hide_field:
                result[key] = serializer.emit_json_for(value, **overrides)
        if self.debug_mode:
            result['$type'] = ".".join([target.__class__.__name__,self._serializer_name])

        return result

class SQLAlchemyJsonSerializer(PropertyJsonSerializer):
    _serializer_name = 'db'

    def get_field_names(self, target):
        for p in target.__mapper__.iterate_properties:
            if p.key.endswith("_id"): continue
            yield [ p.key, None ]
