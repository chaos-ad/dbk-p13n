# -*- coding: utf-8 -*-
'''The app module, containing the app factory function.'''

from flask import Flask

from p13n.settings import DevConfig, ProdConfig
from p13n.extensions import (
    bcrypt,
    cache,
    MatrixConverter
)

import os
import redis


def create_app(config_object=ProdConfig):
    '''
    :param config_object: The configuration object to use.
    '''
    app = Flask(__name__)
    app.config.from_object(config_object)
    register_extensions(app)
    register_errorhandlers(app)
    connect_db(app)
    return app


def register_extensions(app):
    bcrypt.init_app(app)
    cache.init_app(app)
    app.url_map.converters['matrix'] = MatrixConverter
    return None


def register_errorhandlers(app):
    return None


def connect_db(app):
    db_host = app.config.get('REDIS_HOST', 'localhost')
    db_port = app.config.get('REDIS_PORT', '6379')
    app.logger.info("Connecting to the database '%s:%s'..." % (db_host, db_port))
    app.db = redis.StrictRedis(host=db_host, port=db_port, decode_responses=True)
    app.logger.info("Connecting to the database '%s:%s': done." % (db_host, db_port))
    return app


if os.environ.get("P13N_ENV") == 'prod':
    app = create_app(ProdConfig)
else:
    app = create_app(DevConfig)
