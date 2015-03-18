#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
from flask import request, json
from flask_negotiate import consumes, produces

import sys
import logging
import redis

from optparse import OptionParser

#############################################################################

app = Flask(__name__)
logger = logging.getLogger(__name__)

def configure_logging(args):
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(logging.Formatter('%(message)s'))
        stdout_handler.setLevel(logging.INFO)
        logger.addHandler(stdout_handler)
        logger.setLevel(logging.INFO)

        # if args.logfile:
        #       rotate_handler = RotatingFileHandler(args.logfile, maxBytes=10*1024*1024, backupCount=10)
        #       rotate_handler.setLevel(logging.INFO)
        #       app.logger.addHandler(rotate_handler)
        #       app.logger.setLevel(logging.INFO)

#############################################################################

@app.route("/sink", methods=['POST'])
@consumes('application/json')
def handle_sink_post():
        if request.json:
                for record in request.json:
                        logger.info(json.dumps(record))
                return json.jsonify(result={"status": "ok"})
        else:
                # return json.jsonify(error={"message": "json object is expected"})
            pass

#############################################################################


@app.route("/api/RECS/<int:arg_id>", methods=['GET'])
def handle_article_recs(arg_id):
    arg_id = int(str(arg_id)[0:10])
    result = fetch_article_recs(arg_id, 5, 16)
    return json.jsonify(result=result)

@app.route("/api/RECS/<int:arg_id>/<int:min_results>", methods=['GET'])
def handle_article_recs_min(arg_id, min_results):
    arg_id = int(str(arg_id)[0:10])
    result = fetch_article_recs(arg_id, min_results, 16)
    return json.jsonify(result=result)

@app.route("/api/RECS/<int:arg_id>/<int:min_results>/<int:max_results>", methods=['GET'])
def handle_article_recs_minmax(arg_id, min_results, max_results):
    arg_id = int(str(arg_id)[0:10])
    result = fetch_article_recs(arg_id, min_results, max_results)
    return json.jsonify(result=result)


@app.route("/api/RECS/<arg_id>", methods=['GET'])
def handle_user_recs(arg_id):
    result = fetch_user_recs(arg_id, 5, 16)
    return json.jsonify(result=result)

@app.route("/api/RECS/<arg_id>/<int:min_results>", methods=['GET'])
def handle_user_recs_min(arg_id, min_results):
    result = fetch_user_recs(arg_id, min_results, 16)
    return json.jsonify(result=result)

@app.route("/api/RECS/<arg_id>/<int:min_results>/<int:max_results>", methods=['GET'])
def handle_user_recs_minmax(arg_id, min_results, max_results):
    result = fetch_user_recs(arg_id, min_results, max_results)
    return json.jsonify(result=result)

#############################################################################

@app.route("/api/BRAND/<int:arg_id>", methods=['GET'])
def handle_articbrandsecs(arg_id):
    arg_id = int(str(arg_id)[0:10])
    result = fetch_article_brand(arg_id, 1, 16)
    return json.jsonify(result=result)

@app.route("/api/BRAND/<arg_id>", methods=['GET'])
def handle_user_brands(arg_id):
    result = fetch_user_brand(arg_id, 1, 16)
    return json.jsonify(result=result)

@app.route("/api/BRAND/<arg_id>/<int:min_results>", methods=['GET'])
def handle_user_brands_min(arg_id, min_results):
    result = fetch_user_brand(arg_id, min_results, 16)
    return json.jsonify(result=result)

@app.route("/api/BRAND/<arg_id>/<int:min_results>/<int:max_results>", methods=['GET'])
def handle_user_brands_minmax(arg_id, min_results, max_results):
    result = fetch_user_brand(arg_id, min_results, max_results)
    return json.jsonify(result=result)

#############################################################################

@app.route("/api/RECENT/<arg_id>", methods=['GET'])
def handle_user_recent(arg_id):
    result = fetch_user_recent(arg_id, 1, 16)
    return json.jsonify(result=result)

@app.route("/api/RECENT/<arg_id>/<int:min_results>", methods=['GET'])
def handle_user_recent_min(arg_id, min_results):
    result = fetch_user_recent(arg_id, min_results, 16)
    return json.jsonify(result=result)

@app.route("/api/RECENT/<arg_id>/<int:min_results>/<int:max_results>", methods=['GET'])
def handle_user_recent_minmax(arg_id, min_results, max_results):
    result = fetch_user_recent(arg_id, min_results, max_results)
    return json.jsonify(result=result)

#############################################################################
#############################################################################

def fetch_article_recs(id, min_records=5, max_records=16):
    rank = 0
    result = []
    recs = get_article_recs(id, max(min_records, max_records))
    if len(recs) >= min_records:
        pipeline = db.pipeline()
        for article_id, _ in recs[0:max_records]:
            get_article_info(article_id, pipeline)
        article_infos = pipeline.execute()
        for article_id, score in recs[0:max_records]:
            rank += 1
            result.append({ "productMasterSKU": article_id, "rank": rank, "recWeight": score, "attr": article_infos[rank-1]})
    return result

def fetch_user_recs(id, min_records=5, max_records=16):
    rank = 0
    result = []
    recs = get_user_recs(id, max(min_records, max_records))
    if len(recs) >= min_records:
        pipeline = db.pipeline()
        for article_id, _ in recs[0:max_records]:
            get_article_info(article_id, pipeline)
        article_infos = pipeline.execute()
        for article_id, score in recs[0:max_records]:
            rank += 1
            result.append({ "productMasterSKU": article_id, "rank": rank, "recWeight": score, "attr": article_infos[rank-1]})
    return result

#############################################################################

def fetch_article_brand(id, min_records=1, max_records=16):
    return get_article_brand(id)

def fetch_user_brand(id, min_records=1, max_records=16):
    rank = 0
    result = []
    recs = get_user_brands(id, max(min_records, max_records))
    if len(recs) >= min_records:
        for brand, score in recs[0:max_records]:
            rank += 1
            result.append({ "brand": brand, "rank": rank, "weight": score})
    return result

#############################################################################

def fetch_user_recent(id, min_records=1, max_records=16):
    rank = 0
    result = []
    recs = get_user_recent(id, max(min_records, max_records))
    if len(recs) >= min_records:
        pipeline = db.pipeline()
        for article_id in recs[0:max_records]:
            get_article_info(article_id, pipeline)
        article_infos = pipeline.execute()
        for article_id in recs[0:max_records]:
            rank += 1
            result.append({ "productMasterSKU": article_id, "rank": rank, "attr": article_infos[rank-1]})
    return result

#############################################################################
#############################################################################

def get_article_info(id, pipeline=None):
    return (pipeline if pipeline is not None else db).hgetall('%s/INFO' % id)

def get_article_recs(id, limit=-1, pipeline=None):
    return (pipeline if pipeline is not None else db).zrevrangebyscore('%s/RECS' % id, float('+Inf'), float('-Inf'), 0, limit, withscores=True)

def get_article_brand(id, pipeline=None):
    return (pipeline if pipeline is not None else db).get('%s/BRAND' % id)

def get_article_attr(id, pipeline=None):
    return (pipeline if pipeline is not None else db).get('%s/ATTR' % id)

def get_user_recs(id, limit=-1, pipeline=None):
    return (pipeline if pipeline is not None else db).zrevrangebyscore('%s/RECS' % id, float('+Inf'), float('-Inf'), 0, limit, withscores=True)

def get_user_brands(id, limit=-1, pipeline=None):
    return (pipeline if pipeline is not None else db).zrevrangebyscore('%s/BRAND' % id, float('+Inf'), float('-Inf'), 0, limit, withscores=True)

def get_user_recent(id, limit=-1, pipeline=None):
    return (pipeline if pipeline is not None else db).lrange('%s/RECENT' % id, 0, limit)

#############################################################################
#############################################################################

def main():
        parser = OptionParser()
        # parser.add_option("-l", "--logfile", dest = "logfile")
        parser.add_option("-H", "--host", dest = "listen_host", default='127.0.0.1')
        parser.add_option("-P", "--port", dest = "listen_port", type=int, default=5000)
        parser.add_option("-d", "--debug", dest = "debug", default=False, action="store_true")
        parser.add_option("-O", "--db-host", dest = "db_host", default='customer-recs.qxlul7.ng.0001.euw1.cache.amazonaws.com')
        parser.add_option("-R", "--db-port", dest = "db_port", type=int, default=6379)
        args,keys = parser.parse_args()
        args.keys = keys

        global db

        print "Connecting to the database '%s:%s'..." % (args.db_host, args.db_port)
        db = redis.StrictRedis(host=args.db_host, port=args.db_port)
        print "Connecting to the database '%s:%s': done." % (args.db_host, args.db_port)

        configure_logging(args)
        app.run(host=args.listen_host, port=args.listen_port, debug=args.debug)

if __name__ == "__main__":
        main()
