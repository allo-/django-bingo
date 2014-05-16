#!/usr/bin/env python
import json
import sys
import os

from sse import Sse
from flask import Flask, Response
from redis import Redis
redis = Redis()


SITE_ID = int(os.environ['SITE_ID']) if 'SITE_ID' in os.environ else 1


application = Flask(__name__)


def eventstream():
    pubsub = redis.pubsub()
    for event in ['word_votes', 'field_vote', 'num_users', 'num_active_users']:
        pubsub.subscribe(event)

    sse = Sse()
    for message in pubsub.listen():
        if message['type'] != "message":
            continue

        data = json.loads(message['data'])
        if not 'site_id' in data or data['site_id'] != SITE_ID:
            continue

        sse.add_message(message['channel'], str(message['data']))
        for event in sse:
            yield str(event)
        sse.flush()


@application.route("/")
def events():
    response = Response(eventstream(), mimetype="text/event-stream")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


if __name__ == "__main__":
    application.run(threaded=True)
