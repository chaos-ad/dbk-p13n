# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located
in app.py
"""

from flask.ext.bcrypt import Bcrypt
bcrypt = Bcrypt()

from flask.ext.cache import Cache
cache = Cache()
