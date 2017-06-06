# -*- coding: utf-8 -*-

import os
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

    def increment(self):
        self.indent += 1

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
            roomnum = d_data.get("roomnum")
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
handle = list()
roomnum = list()
indent = -1


@app.route("/", methods=["GET"])
def login():
#    global handle, roomnum, indent
    if (request.args.get("name") and request.args.get("roomnum")):
        temp_client = json.dumps({"handle":  request.args.get("name"),
                                  "roomnum": str(request.args.get("roomnum"))
                                  })
        print(temp_client)
        redis.publish(TEMP_CHAN, temp_client)
#        chats.increment()
#        chats.temp_client.append((request.args.get("name"),
#                                  str(request.args.get("roomnum"))
#                                ))
#        handle.append(request.args.get("name"))
#        roomnum.append(str(request.args.get("roomnum")))
#        print("login:", handle[indent], roomnum[indent], indent)
#        print("login:", chats.temp_client[chats.indent])
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/index")
def index():
#    global handle, roomnum, indent
#    print("index:", indent)
#    print("index:", handle[indent], roomnum[indent], indent)
#    print("index:", chats.temp_client[chats.indent])
    index_pubsub = redis.pubsub()
    index_pubsub.subscribe(TEMP_CHAN)
    while(True):
        for client in index_pubsub.listen():
            if client["type"]=="message":
                d_client = json.loads(client)
                print(d_client)
                return render_template("index.html", 
                                       d_client["handle"],
                                       d_client["roomnum"],
                                      )
                break

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
#    global handle, roomnum, indent
#    if (handle and roomnum and handle!=""):
#    print("pre regist:", handle[indent], roomnum[indent], indent)
#    print("regist index:", chats.indent)
#    print("pre regist:", chats.temp_client[chats.indent])
#    chats.register(ws, 
#                   chats.temp_client[chats.indent][0], 
#                   chats.temp_client[chats.indent][1],
#                   )
    out_pubsub = redis.pubsub()
    out_pubsub.subscribe(TEMP_CHAN)
    while(True):
        for client in out_pubsub.listen():
            if client["type"]=="message":
                d_client = json.loads(client)
                print(d_client)
                chats.register(ws, d_client["handle"], d_client["roomnum"])
                break
    app.logger.info(u"regist: {}".format(ws))

    while not ws.closed:
        gevent.sleep(0.1)

def inbox(ws):
    while not ws.closed:
        print(ws.receive())
