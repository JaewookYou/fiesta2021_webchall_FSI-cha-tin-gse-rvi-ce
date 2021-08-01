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
    return flask.redirect(flask.url_for("login"))

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

def doLoginQuery(sock, userid, userpw):
    reqPacket = {
        "command":"login",
        "userid":userid,
        "userpw":userpw
    }
    r="?"
    #r = socksend(sock, reqPacket)
    # return r


@app.route("/login", methods=["GET","POST"])
def login():
    if flask.request.method == "GET":
        ### tmp login 
        
        return flask.render_template("login.html")
    else:
        if "isLogin" in flask.session:
            return flask.redirect(flask.url_for("chat"))

        if "sock" in flask.session:
            flask.session.pop("sock")

        
        t = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        

        flask.session["sock"] = {}
        flask.session["sock"]["s"] = t
        print(flask.session)
        return "123"
        #flask.session["sock"] = t
        
        # flask.session["sock"].connect(("127.0.0.1",9091))

        #doLoginQuery(flask.session["sock"], flask.request.form["uid"], flask.request.form["upw"])
        
        # print(f"[??]{r}")
        # #return flask.render_template("login.html")

        flask.session["id"] = flask.request.form["uid"]
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
    
@app.route("/register", methods=["GET","POST"])
def register():
    if flask.request.method == "GET":
        return flask.render_template("register.html")
    else:
        print("post-register")
        return flask.render_template("register.html")

@app.route("/logout")
def logout():
    flask.session.pop('isLogin', False)
    return flask.redirect(flask.url_for("login"))

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
        print(flask.session)

        flask.session["channel"] = channel
        flask.session["loginid"] = loginid
        flask_socketio.join_room(channel)
        print("joined")

        chatdata["admin"][loginid] = {
            "result": []
        }

        sioemit("join",{"result":"success"}, channel)
    else:
        print("joined fail")
        sioemit("join",{"result":"fail"}, channel)

def socksend(sock, content):
    if type(content) == dict:
        content = json.dumps(content).encode()+b"\n"
    r=""
    try:
        sock.send(content)
        r = sock.recv(4096).decode()
        return json.loads(r)
    except:
        pass

    return r


def sioemit(namespace, content, room=None):
    if room:
        flask_socketio.emit(namespace, content, room=room)
    else:
        flask_socketio.emit(namespace, content)
    return


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
        # print(str(e))
        # print(f"[x] why? {content['to']}:{chatdata[content['to']].keys()}, {flask.session['loginid']}")
        # logging.error(traceback.format_exc())
        pass

    if b"sendtome" in content:
        sendtome_flag = True
    else:
        sendtome_flag = False


    resp = socksend(flask.session["sock"], content)

    if type(resp) != dict:
        resp = {"result": 0, "msg":resp}
    else:
        resp["result"] = 1

    try:
        if sendtome_flag:
            sioemit("newchat", resp, users[flask.session["loginid"]])
        else:
            sioemit("newchat", resp, users[resp["to"]])
            sioemit("newchat", resp, users[resp["from"]])
            print(f'[+] chatsend( to ) - {resp} {users[resp["to"]]}')
            print(f'[+] chatsend(from) - {resp} {users[resp["from"]]}')
    except:
        logging.error(traceback.format_exc())

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
        socket_io.run(app, host="0.0.0.0", debug=True, port=9090)
    except Exception as ex:
        print(ex)