#!/usr/bin/env python
# -*- coding: utf-8 -*-

from p13n import app
from flask import request, json, abort

from functools import wraps


def jsonify():
    def decorated(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return json.jsonify(result=fn(*args, **kwargs))
        return wrapper
    return decorated


class API(object):
    """Basic API stub"""
    prefix = '/api'
    methods = ['GET']
    defaults = None

    def provide(self, url, handler=None):
        def wrapper(h):
            def wraps(**kwargs):
                args = self.defaults.copy()
                args.update(kwargs)
                return h(**args)
            return wraps
        path = self.prefix + url
        handler = self.handle if handler is None else handler
        app.add_url_rule(path, path, wrapper(handler), methods=self.methods)

    def handle(self, **kwargs):
        abort(501)

    def publish(self):
        raise NotImplemented()

    def get_param(self, name, default=None):
        """
        Retrieves a named API parameter.
        Order of scopes to search in:
         * query string
         * headers
         * cookies
        """
        scopes = [request.args, request.headers, request.cookies]
        for s in scopes:
            value = s.get(name)
            if value is not None:
                return value
        return default


class ArticleAPI(API):
    """Article API"""
    prefix = '/api/RECS'
    defaults = {'min_results': 5, 'max_results': 16}

    @jsonify()
    def handle(self, arg_id, min_results, max_results):
        arg_id = int(str(arg_id)[0:10])
        return fetch_article_recs(arg_id, min_results, max_results)

    def publish(self):
        self.provide('/<int:arg_id>')
        self.provide('/<int:arg_id>/<int:min_results>')
        self.provide('/<int:arg_id>/<int:min_results>/<int:max_results>')


class UserAPI(API):
    """User API"""
    prefix = '/api/RECS'
    defaults = {'min_results': 5, 'max_results': 16}

    @jsonify()
    def handle(self, arg_id, min_results, max_results):
        return fetch_user_recs(arg_id, min_results, max_results)

    def publish(self):
        self.provide('/<arg_id>')
        self.provide('/<arg_id>/<int:min_results>')
        self.provide('/<arg_id>/<int:min_results>/<int:max_results>')


class BrandAPI(API):
    """Brand API"""
    prefix = '/api/BRAND'
    defaults = {'min_results': 1, 'max_results': 16}

    @jsonify()
    def handle_article_brand(self, arg_id, **kwargs):
        arg_id = int(str(arg_id)[0:10])
        return fetch_article_brand(arg_id)

    @jsonify()
    def handle(self, arg_id, min_results, max_results):
        return fetch_user_brand(arg_id, min_results, max_results)

    def publish(self):
        self.provide('/<int:arg_id>', self.handle_article_brand)
        self.provide('/<arg_id>')
        self.provide('/<arg_id>/<int:min_results>')
        self.provide('/<arg_id>/<int:min_results>/<int:max_results>')


class RecentAPI(API):
    """Recent API"""
    prefix = '/api/RECENT'
    defaults = {'min_results': 1, 'max_results': 16}

    @jsonify()
    def handle(self, arg_id, min_results, max_results):
        return fetch_user_recent(arg_id, min_results, max_results)

    def publish(self):
        self.provide('/<arg_id>')
        self.provide('/<arg_id>/<int:min_results>')
        self.provide('/<arg_id>/<int:min_results>/<int:max_results>')


class DbModel(object):
    """DB Model"""
    def __init__(self, db):
        self._db = db
        self._pipeline = None

    def db(self):
        if self._pipeline is not None:
            return self._pipeline
        return self._db

    def pipeline(self, f, *args, **kwargs):
        with self._db.pipeline() as self._pipeline:
            try:
                f(*args, **kwargs)
                return self._pipeline.execute()
            finally:
                self._pipeline = None


class DbArticle(DbModel):
    """DbArticle"""
    def __init__(self, db):
        super(DbArticle, self).__init__(db)

    def info(self, id):
        return self.db().hgetall('%s/INFO' % id)

    def brand(self, id):
        return self.db().hgetall('%s/BRAND' % id)

    def attr(self, id):
        return self.db().hgetall('%s/ATTR' % id)

    def infos(self, records):
        return self.pipeline(lambda: [self.info(id) for id in records])

    def records(self, id, limit=-1):
        return self.db().zrevrangebyscore('%s/RECS' % id, float('+Inf'), float('-Inf'), 0, limit, withscores=True)


class DbUser(DbModel):
    """DbUser"""
    def __init__(self, db):
        super(DbUser, self).__init__(db)

    def records(self, id, limit=-1):
        return self.db().zrevrangebyscore('%s/RECS' % id, float('+Inf'), float('-Inf'), 0, limit, withscores=True)

    def brands(self, id, limit=-1):
        return self.db().zrevrangebyscore('%s/BRAND' % id, float('+Inf'), float('-Inf'), 0, limit, withscores=True)

    def recent(self, id, limit=-1):
        return self.db().lrange('%s/RECENT' % id, 0, limit)


def unzip(iter):
    v, _ = zip(*iter)
    return v


def fetch_article_recs(id, min_records=5, max_records=16):
    rank = 0
    result = []
    model = DbArticle(app.db)
    recs = model.records(id, max(min_records, max_records))
    if len(recs) >= min_records:
        article_infos = model.infos(unzip(recs))
        for article_id, score in recs:
            rank += 1
            result.append({"productMasterSKU": article_id, "rank": rank, "recWeight": score, "attr": article_infos[rank - 1]})
    return result


def fetch_user_recs(id, min_records=5, max_records=16):
    rank = 0
    result = []
    recs = DbUser(app.db).records(id, max(min_records, max_records))
    if len(recs) >= min_records:
        article_infos = DbArticle(app.db).infos(unzip(recs))
        for article_id, score in recs:
            rank += 1
            result.append({"productMasterSKU": article_id, "rank": rank, "recWeight": score, "attr": article_infos[rank - 1]})
    return result


def fetch_article_brand(id):
    return DbArticle(app.db).brand(id)


def fetch_user_brand(id, min_records=1, max_records=16):
    rank = 0
    result = []
    recs = DbUser(app.db).brands(id, max(min_records, max_records))
    if len(recs) >= min_records:
        for brand, score in recs:
            rank += 1
            result.append({"brand": brand, "rank": rank, "weight": score})
    return result


def fetch_user_recent(id, min_records=1, max_records=16):
    rank = 0
    result = []
    recs = DbUser(app.db).recent(id, max(min_records, max_records))
    if len(recs) >= min_records:
        article_infos = DbArticle(app.db).infos(recs)
        for article_id in recs:
            rank += 1
            result.append({"productMasterSKU": article_id, "rank": rank, "attr": article_infos[rank - 1]})
    return result


def publish():
    """PUBLISH ALL THE APIS"""
    for api in [ArticleAPI, UserAPI, BrandAPI, RecentAPI]:
        api().publish()


publish()
