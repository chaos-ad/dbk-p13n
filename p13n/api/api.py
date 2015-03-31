#!/usr/bin/env python
# -*- coding: utf-8 -*-

from p13n import app
from flask import request, json, abort, url_for, make_response
from werkzeug.http import parse_range_header
from werkzeug.exceptions import BadRequest
from werkzeug.datastructures import Range, ContentRange


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
    def wrapper(result):
        return json.jsonify(result=result)
    return wrapper


def unwrap(on):
    """
    Response decorator.
    Extracts a specific attribute from each dict in a list returned by the underlying function.
    """
    def wrapper(result):
        return [v[on] for v in result]
    return wrapper


#
# API Definitions

class API(object):
    """
    Basic API stub.
    Serves us to ease defining routing, defining default route fragments and wrapping API handlers.
    """
    prefix = '/p13n/users/<user_id>'
    methods = ['GET']
    decorators = [jsonify()]

    def __init__(self, prefix):
        self.prefix = self.prefix + prefix

    def provide(self, url, handler=None):
        path = self.prefix + url
        handler = self.handle if handler is None else handler
        app.add_url_rule(path, path, handler, methods=self.methods)

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
        scopes = [request.view_args.get('mx', {}), request.args, request.headers, request.cookies]
        for s in scopes:
            value = s.get(name)
            if value is not None:
                return value
        return default

    def require_param(self, name):
        """
        Requires presence of a named API parameter.
        """
        rv = self.get_param(name)
        if rv is None:
            raise BadRequest()
        return rv


class RecommendationAPI(API):
    """
    Recommendation API.
    """
    def __init__(self):
        super(RecommendationAPI, self).__init__('/recommendations')

    def get_resource_range(self, default=(0, None)):
        h = request.headers.get('range')
        v = parse_range_header(h)
        if h is None:
            return Range('resources', [default])
        if (v is None) or (v.units != 'resources') or (len(v.ranges) > 1):
            raise BadRequest()
        return v

    def range_to_scope(self, ranges):
        begin, end = ranges
        if end is None:
            return begin, -1
        return begin, (end - begin)

    def get_content_location(self, user_id, type):
        return url_for(request.endpoint, user_id=user_id, mx={'type': type})

    def get_content_range(self, ranges, length):
        begin, _ = ranges.ranges[0]
        if length == 0:
            return ContentRange(ranges.units, None, None, 0)
        else:
            return ContentRange(ranges.units, begin, begin + length, begin + length)

    def handle(self, handler, decorators=[]):
        def wrapper(user_id, **kwargs):
            ranges = self.get_resource_range()
            if user_id == '-':
                user_id = self.require_param('user_id')
            type = self.require_param('type')
            scope = self.range_to_scope(ranges.ranges[0])
            result = handler(user_id=user_id, type=type, scope=scope)
            if result is None:
                raise BadRequest()
            crange = self.get_content_range(ranges, len(result))
            for fn in decorators:
                result = fn(result)
            response = make_response(result)
            response.headers.add('Content-Location', self.get_content_location(user_id, type))
            response.headers.add('Accept-Range', ranges.units)
            response.headers.add('Content-Range', crange)
            return response
        return wrapper

    def _get_brands(self, user_id, type, scope):
        if type == 'top-brands':
            return DbUser(app.db).get_top_brands(user_id, scope)

    def _get_recommendations(self, user_id, type, scope):
        if type == 'x-sell':
            return DbUser(app.db).get_recommendations(user_id, scope)
        if type == 'recently-viewed':
            return DbUser(app.db).get_recently_viewed(user_id, scope)

    def publish(self):
        default = [jsonify()]
        unwrapped = [unwrap('item')] + default
        self.provide('/brands/<matrix():mx>', self.handle(self._get_brands, decorators=default))
        self.provide('/brands/<matrix():mx>/item', self.handle(self._get_brands, decorators=unwrapped))
        self.provide('/products/<matrix():mx>', self.handle(self._get_recommendations, decorators=default))
        self.provide('/products/<matrix():mx>/item', self.handle(self._get_recommendations, decorators=unwrapped))


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
        return self.db().get('%s/BRAND' % id)

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


class DbUser(DbModel):
    """DbUser"""
    def __init__(self, db):
        super(DbUser, self).__init__(db)
        self.articles = DbArticle(db)

    def records(self, id, scope=(0, -1)):
        begin, limit = scope
        return self.db().zrevrangebyscore('%s/RECS' % id, float('+Inf'), float('-Inf'), begin, limit, withscores=True)

    def brands(self, id, scope=(0, -1)):
        begin, limit = scope
        return self.db().zrevrangebyscore('%s/BRAND' % id, float('+Inf'), float('-Inf'), begin, limit, withscores=True)

    def recent(self, id, scope=(0, -1)):
        begin, limit = scope
        return self.db().lrange('%s/RECENT' % id, begin, limit)

    def get_top_brands(self, id, scope):
        brands = self.brands(id, scope)
        begin, _ = scope
        return [
            Recommendation(n, score, "top-brands", Brand(brand))
                for n, (brand, score) in enumerate(brands, start=begin + 1)
        ]

    def get_recommendations(self, id, scope):
        records = self.records(id, scope)
        infos = self.articles.infos(unzip(records))
        begin, _ = scope
        return [
            Recommendation(n, score, "x-sell", self.articles.get_product_variant(infos[sku]))
                for n, (sku, score) in enumerate(records, start=begin + 1)
        ]

    def get_recently_viewed(self, id, scope):
        records = self.recent(id, scope)
        infos = self.articles.infos(records)
        begin, _ = scope
        return [
            Recommendation(n, 0.0, "recently-viewed", self.articles.get_product_variant(infos[sku]))
                for n, sku in enumerate(records, start=begin + 1)
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
        self['@version'] = '<no-data>'
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
        self['@id'] = self.location + '<no-data>'
        self['name'] = name
        self['description'] = name
        self['url'] = '<no-data>'


#
# API Publishing

for api in [RecommendationAPI]:
    api().publish()
