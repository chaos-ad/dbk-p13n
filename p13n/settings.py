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
    REDIS_HOST = 'customer-recs.qxlul7.ng.0001.euw1.cache.amazonaws.com'
    REDIS_PORT = '6379'


class DevConfig(Config):
    """Development configuration."""
    ENV = 'dev'
    DEBUG = True
    REDIS_HOST = 'localhost'
    REDIS_PORT = '6379'
    # Put the db file in project root
    # DB_PATH = os.path.join(Config.PROJECT_ROOT, DB_NAME)
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.


class TestConfig(Config):
    TESTING = True
    DEBUG = True
