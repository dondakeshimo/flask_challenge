# -*- coding: utf-8 -*-

import os
import redis
import gevent
import json
from flask import Flask, render_template, request
from flask import redirect, url_for
from flask_sockets import Sockets

REDIS_URL = os.environ["REDIS_URL"]
REDIS_CHAN = "chat"

app = Flask(__name__)
app.debug = True

sockets = Sockets(app)
redis = redis.from_url(REDIS_URL)
# redis = redis.Redis()



class ChatBackend(object):

    def __init__(self):
        self.clients = dict()
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(REDIS_CHAN)

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get("data")
            app.logger.info("data from redis: {}".format(data))
            app.logger.info("datatype of data: {}".format(type(data)))
            if message["type"] == "message":
                data = unicode(data, "utf-8")
                app.logger.info(u"Sending message: {}".format(data))
                yield data

    def register(self, client, handle, roomnum):
        self.clients[client] = {
                                "handle":  handle,
                                "roomnum": roomnum,
                                }
        for k,v in self.clients.items():
            app.logger.info("key:", k, "\n", "values:", v)

    def send(self, client, data):
        try:
            d_data = json.loads(data)
            roomnum = d_data["roomnum"]
            if self.clients[client]["roomnum"] == roomnum:
                data = json.dumps(d_data)
                client.send(data)
        except Exception:
            del self.clients[client]

    def run(self):
        for data in self.__iter_data():
            for client in self.clients.keys():
                   gevent.spawn(self.send, client, data)

    def start(self):
        gevent.spawn(self.run)

chats = ChatBackend()
chats.start()
handle = ""
roomnum = ""


@app.route("/", methods=["GET"])
def login():
    global handle, roomnum
    handle  = request.args.get("name")
    roomnum = str(request.args.get("roomnum"))
    if (handle and roomnum):
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/index")
def index():
    global handle, roomnum
    return render_template("index.html", handle=handle, roomnum=roomnum)

@sockets.route("/index/submit")
def inbox(ws):
    while not ws.closed:
        global chats
        gevent.sleep(0.1)
        message = ws.receive()
        app.logger.info("data from ws:", message, type(message))

        if message:
            app.logger.info(u"Inserting message: {}".format(message))
            redis.publish(REDIS_CHAN, message)

@sockets.route("/index/receive")
def outbox(ws):
    global handle, roomnum
    chats.register(ws, handle, roomnum)
    app.logger.info(u"regist: {}".format(ws))

    while not ws.closed:
        gevent.sleep(0.1)

