# -*- coding: utf-8 -*-

import os
import time
import redis
import gevent
import json
from flask import Flask, render_template, request
from flask import redirect, url_for
from flask import make_response
from flask_sockets import Sockets

REDIS_URL = os.environ["REDIS_URL"]
REDIS_CHAN = "chat"
TEMP_CHAN = "temp"

app = Flask(__name__)
app.debug = True

sockets = Sockets(app)
redis = redis.from_url(REDIS_URL)
# redis = redis.Redis()



class ChatBackend(object):

    def __init__(self):
#        self.temp_client = list()
#        self.indent = -1
        self.temp_handle = ""
        self.temp_roomnum = ""
        self.clients = dict()
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(REDIS_CHAN)

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get("data")
            app.logger.info("data from redis: {}".format(data))
            if message["type"] == "message":
                data = unicode(data, "utf-8")
                app.logger.info(u"Sending message: {}".format(data))
                yield data

#    def increment(self):
#        self.indent += 1

    def show_instance(self):
        print(self.temp_handle, self.temp_roomnum)

    def register(self, client, handle, roomnum):
        self.clients[client] = {
                                "handle":  handle,
                                "roomnum": roomnum,
                                }
        for k,v in self.clients.items():
            print("key:", k, "values:", v)

    def send(self, client, data):
        try:
            d_data = json.loads(data)
            roomnum = d_data.get("roomnum", 0)
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


@app.route("/", methods=["GET"])
def login():
    global chats
#    global handle, roomnum, indent
    if (request.args.get("name") and request.args.get("roomnum")):
        chats.temp_handle = request.args.get("name")
        chats.temp_roomnum = str(request.args.get("roomnum"))
        time.sleep(1)
        print("login:", chats.temp_handle, chats.temp_roomnum)
        chats.show_instance()
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/index")
def index():
    global chats
#    global handle, roomnum, indent
    print("index:", chats.temp_handle, chats.temp_roomnum)
    chats.show_instance()
    return render_template("index.html", 
                           handle=chats.temp_handle, 
                           roomnum=chats.temp_roomnum
                           )

@sockets.route("/index/submit")
def inbox(ws):
    while not ws.closed:
        gevent.sleep(0.1)
        message = ws.receive()
        print("data from ws:", message, type(message))

        if message:
            app.logger.info(u"Inserting message: {}".format(message))
            redis.publish(REDIS_CHAN, message)

@sockets.route("/index/receive")
def outbox(ws):
    global chats
#    global handle, roomnum, indent
#    if (handle and roomnum and handle!=""):
    print("regist:", chats.temp_handle, chats.temp_roomnum)
    chats.register(ws, chats.temp_handle, chats.temp_roomnum)
    app.logger.info(u"regist: {}".format(ws))

    while not ws.closed:
        gevent.sleep(0.1)

def inbox(ws):
    while not ws.closed:
        gevent.sleep(0.1)
        print(ws.receive())
