#!/usr/bin/env python
import json
import sys
import os
from sse import Sse
from flask import Flask, Response
from redis import Redis
from gevent import Timeout


SITE_ID = int(os.environ['SITE_ID']) if 'SITE_ID' in os.environ else 1
TIMEOUT = 30

redis = Redis()
application = Flask(__name__)
event_types = ['word_votes', 'field_vote', 'num_users', 'num_active_users']


def eventstream():
    sse = Sse()
    pubsub = redis.pubsub()
    while True:
        for event in event_types:
            pubsub.subscribe(event)
        with Timeout(TIMEOUT) as timeout:
            try:
                for message in pubsub.listen():
                    if message['type'] != "message":
                        continue
                    try:
                        data = json.loads(message['data'])
                    except ValueError:  # broken json
                        continue
                    if 'site_id' not in data or data['site_id'] != SITE_ID:
                        continue

                    sse.add_message(message['channel'], str(message['data']))
                    for event in sse:
                        yield str(event)
                    sse.flush()

                    timeout.cancel()
                    timeout.start()

            # heartbeat, to detect if a user is disconnected
            except Timeout as t:
                if t is not timeout:  # not our timeout
                    raise
                yield ":\n\n"  # heartbeat message

            finally:
                pubsub.close()


@application.route("/")
def events():
    response = Response(eventstream(), mimetype="text/event-stream")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


if __name__ == "__main__":
    application.run(threaded=False, host="0.0.0.0")
