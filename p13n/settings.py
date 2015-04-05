# -*- coding: utf-8 -*-

import os


class Config(object):
    SECRET_KEY = os.environ.get('P13N_SECRET', 'secret-key')  # TODO: Change me
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    BCRYPT_LOG_ROUNDS = 13
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.


class ProdConfig(Config):
    """Production configuration."""
    ENV = 'prod'
    DEBUG = False
    REDIS_HOST = os.environ.get('P13N_REDIS_HOST', '172.30.0.34')
    REDIS_PORT = os.environ.get('P13N_REDIS_PORT', '6379')


class DevConfig(Config):
    """Development configuration."""
    ENV = 'dev'
    DEBUG = True
    REDIS_HOST = os.environ.get('P13N_REDIS_HOST', 'localhost')
    REDIS_PORT = os.environ.get('P13N_REDIS_PORT', '6379')
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.


class TestConfig(Config):
    TESTING = True
    DEBUG = True
