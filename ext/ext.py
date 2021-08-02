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
    r = socksend(sock, reqPacket)
    return r

def sessionCheck(loginCheck=False):   
    if loginCheck:
        if "isLogin" not in flask.session:
            return False
        else:
            return True

    if "isLogin" in flask.session:
        return True

    if "uuid" not in flask.session:
        flask.session["uuid"] = str(uuid.uuid1())

    if flask.session["uuid"] not in users:
        print(f"[+] new socket conn {flask.session['uuid']}")
        users[flask.session["uuid"]] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        users[flask.session["uuid"]].connect(("127.0.0.1",9091))

    return False

@app.route("/login", methods=["GET","POST"])
def login():
    if flask.request.method == "GET":
        if sessionCheck(loginCheck=True):
            return flask.redirect(flask.url_for("chat"))

        return flask.render_template("login.html")
    else:
        if sessionCheck():
            return flask.redirect(flask.url_for("chat"))
        
        queryResult = doLoginQuery(users[flask.session["uuid"]], flask.request.form["userid"], flask.request.form["userpw"])
        if "userid" in queryResult:
            flask.session["userid"] = queryResult["userid"]
            flask.session["isLogin"] = True
            userid = flask.session["userid"]
            chatdata[userid] = {}
            chatdata["admin"] = {}
            chatdata["guest"] = {}
            chatdata["admin"][userid] = {
                "result": []
            }
            chatdata[userid]["admin"] = {
                "result": [
                    {
                        "from": userid,
                        "to": "admin",
                        "date": "2021-06-09 11:01:00",
                        "msg": "hihihi"
                    },
                    {
                        "from": "admin",
                        "to": userid,
                        "date": "2021-06-09 11:01:00",
                        "msg": "asdfasdfasdfsadfasd"
                    }
                ]
            }
            chatdata[userid]["guest"] = {
                "result": []
            }
            chatdata["guest"][userid] = {
                "result": []
            }
            resp = flask.make_response(flask.redirect(flask.url_for("chat")))
            resp.set_cookie('userid', userid)
            resp.set_cookie('uuid', flask.session["uuid"])
            return resp
        else:
            return "login failed"
        
    
@app.route("/register", methods=["GET","POST"])
def register():
    if flask.request.method == "GET":
        if sessionCheck(loginCheck=True):
            return flask.redirect(flask.url_for("chat"))
            
        return flask.render_template("register.html")
    else:
        if sessionCheck():
            return flask.redirect(flask.url_for("chat"))

        return flask.render_template("register.html")

@app.route("/logout")
def logout():
    flask.session.pop('isLogin', False)
    return flask.redirect(flask.url_for("login"))

@app.route("/chat", methods=["GET","POST"])
def chat():
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))        

    if flask.request.method == "GET":
        return flask.render_template("chat.html")

    else:
        if "mode" in flask.request.form:
            mode = flask.request.form.get("mode")
            if mode == "getchatmsg":
                userid = flask.session["userid"]
                chatFrom = flask.request.form.get("id")
                if chatFrom not in chatdata[userid]:
                    chatdata[userid][chatFrom] = {
                        "result": []
                    }
                return chatdata[userid][chatFrom]

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
    userid = data['userid']

    if flask.session["userid"] == userid:
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
        flask.session["userid"] = userid
        flask_socketio.join_room(channel)
        print("joined")

        chatdata["admin"][userid] = {
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

        content["from"] = flask.session["userid"]

        if flask.session["userid"] not in chatdata[content["to"]]:
            chatdata[content["to"]][flask.session["userid"]] = {
                "result": []
            }
        ### tmp database
        chatdata[flask.session["userid"]][content["to"]]["result"].append(content)
        chatdata[content["to"]][flask.session["userid"]]["result"].append(content)
        ###

        content = json.dumps(content).encode()+b"\n"
        
    except Exception as e:
        # print(str(e))
        # print(f"[x] why? {content['to']}:{chatdata[content['to']].keys()}, {flask.session['userid']}")
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
            sioemit("newchat", resp, users[flask.session["userid"]])
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