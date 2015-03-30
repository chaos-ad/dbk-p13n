# -*- coding: utf-8 -*-
"""
Extensions module.
Each extension is initialized in the app factory located in app.py
"""

from werkzeug.routing import BaseConverter, ValidationError

from flask.ext.bcrypt import Bcrypt
bcrypt = Bcrypt()

from flask.ext.cache import Cache
cache = Cache()


class MatrixConverter(BaseConverter):
    def __init__(self, url_map, **defaults):
        super(MatrixConverter, self).__init__(url_map)
        self.defaults = {k: str(v) for k, v in defaults.items()}

    def to_python(self, value):
        if not value.startswith(';'):
            raise ValidationError()
        value = value[1:]
        parts = value.split(';')
        result = self.defaults.copy()
        for part in value.split(';'):
            try:
                key, value = part.split('=')
            except ValueError:
                raise ValidationError()
            result[key.strip()] = value.strip()
        return result

    def to_url(self, value):
        return ';' + ';'.join('{}={}'.format(*item) for item in value.items())
