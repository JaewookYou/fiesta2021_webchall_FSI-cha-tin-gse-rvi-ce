#-*- coding: utf-8 -*-
from flask import Flask, render_template, request as frequest, session, make_response
from flask_socketio import SocketIO, send, emit, join_room, leave_room, rooms
import requests, datetime, uuid, socket, json, threading
import logging, traceback
logging.basicConfig(level=logging.ERROR)

app = Flask(__name__)
app.secret_key = "asdfasdfadsf"
socket_io = SocketIO(app)
chatdata = {}
users = {}


@app.route("/")
def index():
	return render_template("index.html")

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
    if frequest.method == "GET":
        ### tmp login 
        session["id"] = frequest.args["id"]
        loginID = session["id"]
        session["uuid"] = str(uuid.uuid1())
        users[loginID] = session["uuid"]
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
        resp = make_response(render_template("login.html"))
        resp.set_cookie('loginid', loginID)
        resp.set_cookie('uuid', session["uuid"])
        return resp
    else:
        print("post-login")
        return render_template("login.html")
    
@app.route("/register", methods=["GET","POST"])
def register():
    if frequest.method == "GET":
        return render_template("register.html")
    else:
        print("post-register")
        return render_template("register.html")

@app.route("/chat", methods=["GET","POST"])
def chat():
    if frequest.method == "GET":
        return render_template("chat.html")

    else:
        if "mode" in frequest.form:
            mode = frequest.form.get("mode")
            if mode == "getchatmsg":
                loginID = session["id"]
                chatFrom = frequest.form.get("id")
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
def request(data):
    channel = data['channel']
    loginid = data['loginid']
    if users[loginid] == channel:
        if 'server' in data:
            server = data['server']
            t = data['server'].split(':')
            HOST, PORT = t[0], int(t[1])
        else:
            HOST, PORT = '172.16.3.1','9092'
        session["sock"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
        session["sock"].connect((HOST,PORT))

        session["channel"] = channel
        session["loginid"] = loginid
        join_room(channel)
        print("joined")
    else:
        print("joined fail")
        emit("join",{"result":"fail"})

def socksend(sock, data):
    print(data)
    result = b""
    sock.send(data)
    r = sock.recv(1024)
    result += r
    return result

@socket_io.on("chatsend")
def requst(content):
    try:
        if type(content) != dict:
            content = json.loads(content)

        sendfrom = session["loginid"]
        sendto = content["to"]
        sendmsg = content["msg"]
        
        ### tmp database
        chatdata[session["loginid"]][sendto]["result"].append(content)
        chatdata[sendto][session["loginid"]]["result"].append(content)
        ###
        #print(f"[{session['loginid']} -> {sendto}] send finish {chatdata}")
    except Exception as e:
        print(str(e))
        logging.error(traceback.format_exc())
        pass
    print(f"----{session}")
    l = threading.Thread(target=socksend, args=(session["sock"], json.dumps(content).encode()+b"\n"))
    l.start()
    #print(f"send complete{users}")
    if "sendtome" in content:
        emit("newchat", content, room=users[session["loginid"]])
    else:
        emit("newchat", content, room=users[sendto])
    #print("real send complete!!!")


@socket_io.on("testsend")
def testsend(data):
    print(data)
    msg = data["msg"]
    sendto = data["to"]
    sendfrom = data["from"]
    chatdict = makechat(sendfrom, sendto, msg)
    chatdata[sendfrom][session["loginid"]]["result"].append(chatdict)
    chatdata[session["loginid"]][sendfrom]["result"].append(chatdict)

    emit("newchat", chatdict, room=session["channel"])
    emit("newchat", chatdict, room=users[sendto])
    return "true"

@socket_io.on("connect")
def connected():
    print("connected")

    #sock.close()

@socket_io.on("disconnect")
def disconnected():
    print("disconnected")
    session["sock"].close()
    print(session["sock"])


if __name__ == "__main__":
    try:
        #app.run(host="0.0.0.0", port=9090, debug=True)
        socket_io.run(app, host="0.0.0.0", debug=True, port=9090)
    except Exception as ex:
        print(ex)