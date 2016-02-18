# -*- coding: utf-8 -*-

from flask.ext.babelex import lazy_gettext, gettext
from flask import request

from segue.core import config

# Aliases
_l = lazy_gettext
_ = gettext

def get_locale():
    return request.\
        accept_languages.best_match(config.LANGUAGES or 'pt')