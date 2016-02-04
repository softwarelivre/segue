from werkzeug.utils import ImportStringError
import logging, logging.handlers
import flask
from flask.ext.cors import CORS

import core
import api
import json
import errors


class NullApplication(flask.Flask):
    def __init__(self):
        super(NullApplication, self).__init__(__name__)

class Application(flask.Flask):
    def __init__(self, settings_override=None, blueprints=True):
        super(Application, self).__init__(__name__)
        self._load_configs(settings_override)
        self._set_logger()
        self._set_json_encoder()
        self._set_debug()
        if blueprints: self._register_blueprints()
        self._register_error_handlers()
        self._init_deps()
        self._load_cors()
        self._load_babel()

    def _load_configs(self, settings_override):
        try:
            self.config.from_object('segue.settings')
        except ImportStringError, e:
            pass
        self.config.from_object(settings_override)
        core.config.init_app(self)

    def _set_logger(self):
        formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

        handler = logging.handlers.RotatingFileHandler(self.config['LOGFILE'],
                                                       maxBytes=10000000, backupCount=10, mode="a+")
        handler.setLevel(getattr(logging, self.config['LOGLEVEL']))
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        core.logger.init_app(self)
        core.logger.info('SEGUE HAS STARTED (well, at least we have a logger to speak of)');

    def _load_cors(self):
        self.cors = CORS(self)

    def _load_babel(self):
        def get_locale():
            return flask.request.\
                accept_languages.best_match(core.config.LANGUAGES or 'pt')

        core.babel.init_app(self)
        core.babel.locale_selector_func = get_locale

    def _register_error_handlers(self):
        def handler(e):
            return flask.jsonify(dict(errors=e)), getattr(e, 'code', 400)
        self.errorhandler(errors.SegueError)(handler)

    def _set_debug(self):
        self.debug = True

    def _register_blueprints(self):
        for blueprint in api.load_blueprints():
            self.register_blueprint(blueprint)

    def _init_deps(self):
        core.db.init_app(self)
        core.jwt.init_app(self)
        core.mailer.init_app(self)
        core.cache.init_app(self)

    def _set_json_encoder(self):
        self.json_encoder = json.JSONEncoder
