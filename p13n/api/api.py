#!/usr/bin/env python
# -*- coding: utf-8 -*-

from p13n import app
from flask import request, json, abort

from functools import wraps


def unzip(iter):
    """
    Unzips a list of tuples.
    Returns list formed out of first element of each tuple.
    """
    v, _ = zip(*iter)
    return v


def jsonify():
    """
    Response decorator.
    Makes up a JSON response given call result of the underlying function, usually a dict.
    """
    def decorated(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return json.jsonify(result=fn(*args, **kwargs))
        return wrapper
    return decorated


def unwrap(on):
    """
    Response decorator.
    Extracts a specific attribute from each dict in a list returned by the underlying function.
    """
    def decorated(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return [v[on] for v in fn(*args, **kwargs)]
        return wrapper
    return decorated


#
# API Definitions

class API(object):
    """
    Basic API stub.
    Serves us to ease defining routing, defining default route fragments and wrapping API handlers.
    """
    prefix = '/api'
    methods = ['GET']
    defaults = None

    def provide(self, url, handler=None):
        def wrapper(h):
            def wraps(**kwargs):
                args = self.defaults.copy() if self.defaults is not None else {}
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
    """
    Article API.
    """
    prefix = '/api/RECS'
    defaults = {'min_results': 5, 'max_results': 16}

    def _handle(self, arg_id, min_results, max_results):
        arg_id = int(str(arg_id)[0:10])
        limit = max(min_results, max_results)
        return DbArticle(app.db).get_recommendations(arg_id, min_results, limit)

    @jsonify()
    def handle(self, **kwargs):
        return self._handle(**kwargs)

    @jsonify()
    @unwrap(on='item')
    def handle_unwrapped(self, **kwargs):
        return self._handle(**kwargs)

    def publish(self):
        self.provide('/<int:arg_id>')
        self.provide('/<int:arg_id>/<int:min_results>')
        self.provide('/<int:arg_id>/<int:min_results>/<int:max_results>')
        # How to handle these properly?
        # Follow API docs closer?
        self.provide('/unwrap/<int:arg_id>', self.handle_unwrapped)
        self.provide('/unwrap/<int:arg_id>/<int:min_results>', self.handle_unwrapped)
        self.provide('/unwrap/<int:arg_id>/<int:min_results>/<int:max_results>', self.handle_unwrapped)


class UserAPI(API):
    """
    User API.
    """
    prefix = '/api/RECS'
    defaults = {'min_results': 5, 'max_results': 16}

    def _handle(self, arg_id, min_results, max_results):
        limit = max(min_results, max_results)
        return DbUser(app.db).get_recommendations(arg_id, min_results, limit)

    @jsonify()
    def handle(self, **kwargs):
        return self._handle(**kwargs)

    @jsonify()
    @unwrap(on='item')
    def handle_unwrapped(self, **kwargs):
        return self._handle(**kwargs)

    def publish(self):
        self.provide('/<arg_id>')
        self.provide('/<arg_id>/<int:min_results>')
        self.provide('/<arg_id>/<int:min_results>/<int:max_results>')
        self.provide('/unwrap/<arg_id>', self.handle_unwrapped)
        self.provide('/unwrap/<arg_id>/<int:min_results>', self.handle_unwrapped)
        self.provide('/unwrap/<arg_id>/<int:min_results>/<int:max_results>', self.handle_unwrapped)


class BrandAPI(API):
    """
    Brand API.
    """
    prefix = '/api/BRAND'
    defaults = {'min_results': 1, 'max_results': 16}

    def _handle(self, arg_id, min_results, max_results):
        limit = max(min_results, max_results)
        return DbUser(app.db).get_top_brands(arg_id, min_results, limit)

    @jsonify()
    def handle_article_brand(self, arg_id, **kwargs):
        arg_id = int(str(arg_id)[0:10])
        return DbArticle(app.db).brand(arg_id)

    @jsonify()
    def handle(self, **kwargs):
        return self._handle(**kwargs)

    @jsonify()
    @unwrap(on='item')
    def handle_unwrapped(self, **kwargs):
        return self._handle(**kwargs)

    def publish(self):
        # Not quite well-formed route:
        #  - db contains just a string under any article brand key;
        #  - could easily match earlier errorneously.
        # What to do with it? Commented out for now.
        # self.provide('/<int:arg_id>', self.handle_article_brand)
        self.provide('/<arg_id>')
        self.provide('/<arg_id>/<int:min_results>')
        self.provide('/<arg_id>/<int:min_results>/<int:max_results>')
        self.provide('/unwrap/<arg_id>', self.handle_unwrapped)
        self.provide('/unwrap/<arg_id>/<int:min_results>', self.handle_unwrapped)
        self.provide('/unwrap/<arg_id>/<int:min_results>/<int:max_results>', self.handle_unwrapped)


class RecentAPI(API):
    """
    Recent API.
    """
    prefix = '/api/RECENT'
    defaults = {'min_results': 1, 'max_results': 16}

    def _handle(self, arg_id, min_results, max_results):
        limit = max(min_results, max_results)
        return DbUser(app.db).get_recently_viewed(arg_id, min_results, limit)

    @jsonify()
    def handle(self, **kwargs):
        return self._handle(**kwargs)

    @jsonify()
    @unwrap(on='item')
    def handle_unwrapped(self, **kwargs):
        return self._handle(**kwargs)

    def publish(self):
        self.provide('/<arg_id>')
        self.provide('/<arg_id>/<int:min_results>')
        self.provide('/<arg_id>/<int:min_results>/<int:max_results>')
        self.provide('/unwrap/<arg_id>', self.handle_unwrapped)
        self.provide('/unwrap/<arg_id>/<int:min_results>', self.handle_unwrapped)
        self.provide('/unwrap/<arg_id>/<int:min_results>/<int:max_results>', self.handle_unwrapped)


#
# Database accessors

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

    def infos(self, ids):
        return dict(zip(ids, self.pipeline(lambda: [self.info(id) for id in ids])))

    def records(self, id, limit=-1):
        return self.db().zrevrangebyscore('%s/RECS' % id, float('+Inf'), float('-Inf'), 0, limit, withscores=True)

    def get_product_variant(self, info):
        return ProductVariant(
            info['defaultVariation'],
            info['shortDesc'],
            brand=Brand(info['manufacturer']),
            price=UnitPriceSpecification(info['salePrice'], type='SALE_PRICE'),
            image_url=info['effectiveUrl']
        )

    def get_recommendations(self, id, at_least=-1, at_most=-1):
        records = self.records(id, at_most)
        if len(records) < at_least:
            return []
        infos = self.infos(unzip(records))
        print (infos)
        return [
            Recommendation(n, score, "x-sell", self.get_product_variant(infos[sku]))
                for n, (sku, score) in enumerate(records, start=1)
        ]


class DbUser(DbModel):
    """DbUser"""
    def __init__(self, db):
        super(DbUser, self).__init__(db)
        self.articles = DbArticle(db)

    def records(self, id, limit=-1):
        return self.db().zrevrangebyscore('%s/RECS' % id, float('+Inf'), float('-Inf'), 0, limit, withscores=True)

    def brands(self, id, limit=-1):
        return self.db().zrevrangebyscore('%s/BRAND' % id, float('+Inf'), float('-Inf'), 0, limit, withscores=True)

    def recent(self, id, limit=-1):
        return self.db().lrange('%s/RECENT' % id, 0, limit)

    def get_top_brands(self, id, at_least=-1, at_most=-1):
        brands = self.brands(id, at_most)
        if len(brands) < at_least:
            return []
        return [
            Recommendation(n, score, "top-brands", Brand(brand))
                for n, (brand, score) in enumerate(brands, start=1)
        ]

    def get_recommendations(self, id, at_least=-1, at_most=-1):
        records = self.records(id, at_most)
        if len(records) < at_least:
            return []
        infos = self.articles.infos(unzip(records))
        return [
            Recommendation(n, score, "x-sell", self.articles.get_product_variant(infos[sku]))
                for n, (sku, score) in enumerate(records, start=1)
        ]

    def get_recently_viewed(self, id, at_least=-1, at_most=-1):
        records = self.recent(id, at_most)
        if len(records) < at_least:
            return []
        infos = self.articles.infos(records)
        return [
            Recommendation(n, 0.0, "recently-viewed", self.articles.get_product_variant(infos[sku]))
                for n, sku in enumerate(records, start=1)
        ]


#
# API Resource views

class Recommendation(dict):
    def __init__(self, rank, weight, type, item):
        super(Recommendation, self).__init__()
        self['@type'] = self.__class__.__name__
        self['rank'] = rank
        self['weight'] = weight
        self['type'] = type
        self['item'] = item


class UnitPriceSpecification(dict):
    def __init__(self, price, type='SALE_PRICE', currency='EUR'):
        super(UnitPriceSpecification, self).__init__()
        self['@type'] = self.__class__.__name__
        self['price'] = price
        self['type'] = type
        self['priceCurrency'] = currency


class ProductVariant(dict):
    location = '/catalogue/products/'

    def __init__(self, sku, description, brand, price, image_url):
        super(ProductVariant, self).__init__()
        self['@type'] = self.__class__.__name__
        self['@id'] = self.location + sku
        self['@version'] = '?'
        self['url'] = 'http://example.com/'
        self['sku'] = sku
        self['master'] = {'@id': self.location + self.master()}
        self['description'] = description
        self['brand'] = brand
        self['image'] = image_url
        self['priceSpecifications'] = [price]
        self['signage'] = []

    def master(self):
        return self['sku'][0:10]


class Brand(dict):
    location = '/catalogue/brands/'

    def __init__(self, name):
        super(Brand, self).__init__()
        self['@type'] = self.__class__.__name__
        self['@id'] = self.location + '?'
        self['name'] = name
        self['description'] = name
        self['url'] = 'http://example.com/'


#
# API Publishing

for api in [ArticleAPI, UserAPI, BrandAPI, RecentAPI]:
    api().publish()
