from flask import url_for
from segue.json import SimpleJson


from flask_sqlalchemy import Model
from flask_sqlalchemy import Pagination

class Response(object):

    def __init__(self, data, schema):
        self.data = data
        self.schema = schema

    def create(self):
        if isinstance(self.data, Model) or isinstance(self.data, dict):
            result = self.schema().dump(self.data).data
            return {'resource': result}
        elif isinstance(self.data, list):
            result = self.schema(many=True).dump(self.data).data
            return {'count': len(result), 'items': result}
        elif isinstance(self.data, Pagination):
            result = self.schema(many=True).dump(self.data.items).data
            return {
                'items': result, 
                'total': self.data.total, 
                'page':  self.data.page, 
                'per_page': self.data.per_page
            }
        else:
            raise ValueError("Invalid data type")

class BaseResponse(SimpleJson):
    @classmethod
    def create(cls, list_or_entity, *args, **kw):
        if isinstance(list_or_entity, list):
            return [ cls(e, *args, **kw) for e in list_or_entity ]
        if list_or_entity:
            return cls(list_or_entity, *args, **kw)

    def __init__(self):
        self.__dict__["$type"] = self.__class__.__name__

    def add_link(self, name, collection_or_entity, route='', **route_parms):
        if not hasattr(self, 'links'):
            self.links = {}
        if collection_or_entity is None: return
        self.links[name] = { "href": url_for(route, **route_parms) }
        if isinstance(collection_or_entity, int) and collection_or_entity >= 0:
            self.links[name]['count'] = collection_or_entity
        elif isinstance(collection_or_entity, list):
            self.links[name]['count'] = len(collection_or_entity)


