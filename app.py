# -*- coding: utf-8 -*-

import os
import redis
import gevent
from flask import Flask, render_template, request
from flask_sockets import Sockets

# REDIS_URL = os.environ["REDIS_URL"]
REDIS_CHAN = "chat"

app = Flask(__name__)
app.debug = True

sockets = Sockets(app)
# redis = redis.from_url(REDIS_URL)
redis = redis.Redis()



class ChatBackend(object):

    def __init__(self):
        self.clients = list()
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(REDIS_CHAN)

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get("data")
            print(data, type(data))
            if message["type"] == "message":
                data = unicode(data, "utf-8")
                app.logger.info(u"Sending message: {}".format(data))
                yield data

    def register(self, client):
        self.clients.append(client)

    def send(self, client, data):
        try:
            client.send(data)
        except Exception:
            self.clients.remove(client)

    def run(self):
        for data in self.__iter_data():
            for client in self.clients:
                gevent.spawn(self.send, client, data)

    def start(self):
        gevent.spawn(self.run)

chats = ChatBackend()
chats.start()


@app.route("/", methods=["GET"])
def login():
    print(request.headers)
    print("body: {}".format(request.data))
    return render_template("login.html")


#@app.route("/")
#def hello():
#    name = "taku"
#    return render_template("index.html", handlename=name)

@sockets.route("/submit")
def inbox(ws):
    while not ws.closed:
        gevent.sleep(0.1)
        message = ws.receive()
        print(message)

        if message:
            app.logger.info(u"Inserting message: {}".format(message))
            redis.publish(REDIS_CHAN, message)

@sockets.route("/receive")
def outbox(ws):
    chats.register(ws)
    print(ws)

    while not ws.closed:
        gevent.sleep(0.1)

