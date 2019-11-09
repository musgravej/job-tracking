import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.urandom(24)


class ProductionConfig(Config):
    DEBUG = False


class DevelopConfig(Config):
    DEBUG = True


config = {
    'default': Config,
    'development': DevelopConfig,
    'production': ProductionConfig,
}