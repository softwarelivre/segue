# -*- coding: utf-8 -*-

from segue.schema import Field

search_args = {
    'sort': Field.str(),
    'page': Field.int(missing=1),
    'per_page':  Field.int(missing=25)
}
