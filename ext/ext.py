#-*- coding: latin-1 -*-
# from flask import Flask, flask.render_template, request as flask.request, flask.session, flask.make_response
# #from flask_socketio import SocketIO, send, emit, join_room, leave_room, rooms
import flask_socketio
import flask
import requests, datetime, uuid, socket, json, threading
import logging, traceback
import concurrent.futures 
from threading import Lock
logging.basicConfig(level=logging.ERROR)

app = flask.Flask(__name__)
app.secret_key = "asdfasdfadsf"
socket_io = flask_socketio.SocketIO(app)
chatdata = {}
users = {}

block = Lock()

@app.route("/")
def index():
    return flask.render_template("index.html")

@app.route("/getlist", methods=["GET"])
def getlist():
    data = {
        "result":[
            {
                "id" : "admin",
                "date" : "Jul 17",
                "text" : "hello there"
            },
            {
                "id" : "guest",
                "date" : "Jul 16",
                "text" : "this is guest"
            }
        ]
    }
    return data

@app.route("/login", methods=["GET","POST"])
def login():
    if flask.request.method == "GET":
        ### tmp login 
        flask.session["id"] = flask.request.args["id"]
        loginID = flask.session["id"]
        flask.session["uuid"] = str(uuid.uuid1())
        users[loginID] = flask.session["uuid"]
        chatdata[loginID] = {}
        chatdata["admin"] = {}
        chatdata["guest"] = {}
        chatdata["admin"][loginID] = {
            "result": []
        }
        chatdata[loginID]["admin"] = {
            "result": [
                {
                    "from": loginID,
                    "to": "admin",
                    "date": "2021-06-09 11:01:00",
                    "msg": "hihihi"
                },
                {
                    "from": "admin",
                    "to": loginID,
                    "date": "2021-06-09 11:01:00",
                    "msg": "asdfasdfasdfsadfasd"
                }
            ]
        }
        chatdata[loginID]["guest"] = {
            "result": []
        }
        chatdata["guest"][loginID] = {
            "result": []
        }
        resp = flask.make_response(flask.render_template("login.html"))
        resp.set_cookie('loginid', loginID)
        resp.set_cookie('uuid', flask.session["uuid"])
        return resp
    else:
        print("post-login")
        return flask.render_template("login.html")
    
@app.route("/register", methods=["GET","POST"])
def register():
    if flask.request.method == "GET":
        return flask.render_template("register.html")
    else:
        print("post-register")
        return flask.render_template("register.html")

@app.route("/chat", methods=["GET","POST"])
def chat():
    if flask.request.method == "GET":
        return flask.render_template("chat.html")

    else:
        if "mode" in flask.request.form:
            mode = flask.request.form.get("mode")
            if mode == "getchatmsg":
                loginID = flask.session["id"]
                chatFrom = flask.request.form.get("id")
                if chatFrom not in chatdata[loginID]:
                    chatdata[loginID][chatFrom] = {
                        "result": []
                    }
                return chatdata[loginID][chatFrom]

        else:
            return "[external server] mode parameter doesn't exist"

def makechat(sendfrom, sendto, sendmsg):
    date = datetime.datetime.strftime(datetime.datetime.now(),"%Y-%m-%d %H:%M:%S")
    chatdict = {
        "from": sendfrom,
        "to": sendto,
        "date": date,
        "msg": sendmsg
    }
    return chatdict


@socket_io.on("join")
def join(data):
    channel = data['channel']
    loginid = data['loginid']
    if users[loginid] == channel:
        if 'chatserver' in data:
            chatserver = data['chatserver']
            t = chatserver.split(':')
            c = (t[0], int(t[1]))
        else:
            c = ('127.0.0.1', 9091)
        print(c)
        flask.session["sock"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
        flask.session["sock"].connect(c)

        flask.session["channel"] = channel
        flask.session["loginid"] = loginid
        flask_socketio.join_room(channel)
        print("joined")

        chatdata["admin"][loginid] = {
            "result": []
        }

        flask_socketio.emit("join",{"result":"success"}, room=channel)
    else:
        print("joined fail")
        flask_socketio.emit("join",{"result":"fail"}, room=channel)

def socksend(sock, content):
    r=""
    try:
        sock.send(content)
        r = sock.recv(4096)
        return json.loads(r)
    except:
        pass

    return r

def stopPool(e):
    for pid, process in e._processes.items():
        print(f"[+] {pid}:{process} killed..")
        #e.terminate()
    e.shutdown()

@socket_io.on("chatsend")
def chatsend(content):
    try:
        if type(content) != dict:
            content = content.encode('latin-1')
            content = json.loads(content)

        content["from"] = flask.session["loginid"]

        if flask.session["loginid"] not in chatdata[content["to"]]:
            chatdata[content["to"]][flask.session["loginid"]] = {
                "result": []
            }
        ### tmp database
        chatdata[flask.session["loginid"]][content["to"]]["result"].append(content)
        chatdata[content["to"]][flask.session["loginid"]]["result"].append(content)
        ###

        content = json.dumps(content).encode()+b"\n"
        
    except Exception as e:
        print(str(e))
        print(f"[x] why? {content['to']}:{chatdata[content['to']].keys()}, {flask.session['loginid']}")
        logging.error(traceback.format_exc())
        pass

    if b"sendtome" in content:
        sendtome_flag = True
    else:
        sendtome_flag = False

    with concurrent.futures.ProcessPoolExecutor(max_workers=1) as e:
        try:
            f = e.submit(socksend, flask.session["sock"], content)
            resp = f.result()
            print(resp)
            stopPool(e)
        except concurrent.futures._base.TimeoutError:
            stopPool(e)
        except:
            stopPool(e)

    if type(resp) != dict:
        resp = {"result": 0, "msg":resp}
    else:
        resp["result"] = 1

    if sendtome_flag:
        flask_socketio.emit("newchat", resp, room=users[flask.session["loginid"]])
    else:
        try:
            flask_socketio.emit("newchat", resp, room=users[resp["to"]])
        except:
            logging.error(traceback.format_exc())
            print(f"[x] why!! {resp} -> {users}")
        flask_socketio.emit("newchat", resp, room=users[resp["from"]])
        print(f'[+] chatsend - {users[resp["to"]]}')
        print(f'[+] chatsend - {users[resp["from"]]}')


@socket_io.on("testsend")
def testsend(data):
    print(data)
    msg = data["msg"]
    sendto = data["to"]
    sendfrom = data["from"]
    chatdict = makechat(sendfrom, sendto, msg)
    chatdata[sendfrom][flask.session["loginid"]]["result"].append(chatdict)
    chatdata[flask.session["loginid"]][sendfrom]["result"].append(chatdict)

    flask_socketio.emit("newchat", chatdict, room=flask.session["channel"])
    flask_socketio.emit("newchat", chatdict, room=users[sendto])
    return "true"

@socket_io.on("connect")
def connected():
    print("connected")

@socket_io.on("disconnect")
def disconnected():
    print("disconnected")
    flask.session["sock"].close()
    print(flask.session["sock"])


if __name__ == "__main__":
    try:
        #app.run(host="0.0.0.0", port=9090, debug=True)
        socket_io.run(app, host="0.0.0.0", debug=True, port=9090)
    except Exception as ex:
        print(ex)