# -*- coding: utf-8 -*-

import os


class Config(object):
    SECRET_KEY = os.environ.get('P13N_SECRET', 'secret-key')  # TODO: Change me
    LISTEN_PORT = os.environ.get('P13N_LISTEN_PORT', '5000')
    LISTEN_HOST = os.environ.get('P13N_LISTEN_HOST', '0.0.0.0')
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    BCRYPT_LOG_ROUNDS = 13
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.

class ProdConfig(Config):
    """Production configuration."""
    ENV = 'prod'
    DEBUG = False
    REDIS_PORT = os.environ.get('P13N_REDIS_PORT', '6379')
    REDIS_HOST = os.environ.get('P13N_REDIS_HOST', 'customer-recs.qxlul7.ng.0001.euw1.cache.amazonaws.com')

class DevConfig(Config):
    """Development configuration."""
    ENV = 'dev'
    DEBUG = True
    REDIS_PORT = os.environ.get('P13N_REDIS_PORT', '6379')
    REDIS_HOST = os.environ.get('P13N_REDIS_HOST', 'localhost')

class TestConfig(Config):
    TESTING = True
    DEBUG = True
