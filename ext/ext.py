#-*- coding: latin-1 -*-
import flask_socketio
import flask
import requests, datetime, uuid, socket, json, threading, os, base64, re
import logging, traceback
logging.basicConfig(level=logging.ERROR)

app = flask.Flask(__name__)
app.secret_key = "asdfasdfadsf"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
socket_io = flask_socketio.SocketIO(app)
chatdata = {}
users = {}
block = threading.Lock()


# -*-*-*-*-* common methods *-*-*-*-*- #

def doLoginQuery(sock, userid, userpw):
    reqPacket = {
        "command":"login",
        "userid":userid,
        "userpw":userpw
    }
    r = socksend(sock, reqPacket)
    return r

def doRegisterQuery(sock, userid, userpw, filename, profileImageContent):
    reqPacket = {
        "command":"register",
        "userid":userid,
        "userpw":userpw,
        "filename":filename,
        "profileImageContent": profileImageContent
    }
    r= socksend(sock, reqPacket)
    return r

def checkUserIDPW(userid, userpw):
    if re.search(r"[^\w]",userid) or len(userid) == 0 or len(userid) > 50 or len(userpw) == 0 or len(userpw) > 50:
        return False
    else:
        return True
        
def secureFileName(filename):
    filteringList = ["..","\\","\x00","'",'"']
    for filterChar in filteringList:
        filename = filename.replace(filterChar, "")
    return filename

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


def socksend(sock, content):
    if type(content) == dict:
        content = json.dumps(content).encode()+b"\n"
    r=""
    try:
        with block:
            sock.send(content)
            r = sock.recv(1024*1024*80).decode('latin-1')
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


# -*-*-*-*-* flask methods *-*-*-*-*- #

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

@app.route("/logout")
def logout():
    flask.session.pop('isLogin', False)
    return flask.redirect(flask.url_for("login"))

@app.route("/chat", methods=["GET"])
def chat():
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))

    return flask.render_template("chat.html")


@app.route("/login", methods=["GET","POST"])
def login():
    if flask.request.method == "GET":
        if sessionCheck(loginCheck=True):
            return flask.redirect(flask.url_for("chat"))
        
        try:
            msg = flask.request.args["msg"]
        except:
            msg = "false"

        return flask.render_template("login.html", msg=msg)
    else:
        if sessionCheck():
            return flask.redirect(flask.url_for("chat"))

        if not checkUserIDPW(flask.request.form["userid"], flask.request.form["userpw"]):
            return flask.render_template("login.html", msg="invalid userid or userpw")
        
        queryResult = doLoginQuery(users[flask.session["uuid"]], flask.request.form["userid"], flask.request.form["userpw"])
        if "userid" in queryResult:
            flask.session["userid"] = queryResult["userid"]
            flask.session["isLogin"] = True
            userid = flask.session["userid"]
            users[userid] = flask.session["uuid"]
            
            resp = flask.make_response(flask.redirect(flask.url_for("chat")))
            resp.set_cookie('userid', userid)
            resp.set_cookie('uuid', flask.session["uuid"])
            return resp
        else:
            return flask.render_template("login.html", msg="login failed")

    
@app.route("/register", methods=["GET","POST"])
def register():
    if flask.request.method == "GET":
        if sessionCheck(loginCheck=True):
            return flask.redirect(flask.url_for("chat"))
            
        return flask.render_template("register.html")
    else:
        if sessionCheck():
            return flask.redirect(flask.url_for("chat"))

        if not checkUserIDPW(flask.request.form["userid"], flask.request.form["userpw"]):
            return flask.render_template("login.html", msg="invalid userid or userpw")

        profileImageFile = flask.request.files["profileImage"]
        if profileImageFile.filename == "":
            resp = "[x] please attach a profile image"
            return flask.redirect(flask.url_for("login", msg=resp))
        
        fileContent = base64.b64encode(profileImageFile.read())
        if type(fileContent) == bytes:
            fileContent = fileContent.decode()

        resp = doRegisterQuery(
            users[flask.session["uuid"]], 
            flask.request.form["userid"], 
            flask.request.form["userpw"], 
            profileImageFile.filename,
            fileContent 
        )

        return flask.redirect(flask.url_for("login", msg=resp))

@app.route("/getProfileImage", methods=["GET"])
def getProfileImage():
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))

    userid = flask.request.args['id']

    reqPacket = {
        "command":"getProfileImage",
        "userid":userid
    }
    r= socksend(users[flask.session["uuid"]], reqPacket)
    return r



# -*-*-*-*-* socket.io methods *-*-*-*-*- #

@socket_io.on("join")
def join(content):
    channel = content['channel']
    userid = content['userid']

    if flask.session["userid"] == userid and flask.session["uuid"] == channel:
        if 'chatserver' in content:
            if flask.session["uuid"] in users:
                users[flask.session["uuid"]].close()
            
            chatserver = content['chatserver']
            t = chatserver.split(':')
            c = (t[0], int(t[1]))
            
            users[flask.session["uuid"]] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
            users[flask.session["uuid"]].connect(c)

        flask.session["channel"] = channel
        flask_socketio.join_room(channel)

        sioemit("join",{"result":"success"}, channel)
    else:
        sioemit("join",{"result":"fail"}, channel)

@socket_io.on("getlist")
def getlist(content):
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))

    try:
        if type(content) != dict:
            content = content.encode('latin-1')
            content = json.loads(content)

        if content["from"] != flask.session["userid"]:
            print(f"[x] {content['from']} != {flask.session['userid']}")
            return "[x] request from user is different from session"

    except Exception as e:
        logging.error(traceback.format_exc())
        pass

    resp = socksend(users[flask.session["uuid"]], content)
    print(resp)
    sioemit("getlist", resp, users[flask.session["userid"]])

@socket_io.on("getchatmsg")
def getchatmsg(content):
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))

    try:
        if type(content) != dict:
            content = content.encode('latin-1')
            content = json.loads(content)

        if content["from"] != flask.session["userid"]:
            print(f"[x] {content['from']} != {flask.session['userid']}")
            return "[x] request from user is different from session"

    except Exception as e:
        logging.error(traceback.format_exc())
        pass

    resp = socksend(users[flask.session["uuid"]], content)

    sioemit("getchatmsg", resp, users[flask.session["userid"]])


@socket_io.on("imagesend")
def imagesend(content):        
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))
    resp = ""

    if content["from"] != flask.session["userid"]:
        print(f"[x] {content['from']} != {flask.session['userid']}")
        return "[x] request from user is different from session"

    uploadPath = ""
    uploadFileRoot = f"{os.path.abspath('./')}/uploads/{content['from']}/"
    if not os.path.exists(uploadFileRoot) and not os.path.isdir(uploadFileRoot):
        os.makedirs(uploadFileRoot)

    filename = secureFileName(content['filename'])
    
    if filename == "":
        resp = f"[x] please attach a image"
        return resp

    uploadFilePath = uploadFileRoot + filename

    try:
        with open(uploadFilePath, 'wb') as f:
            f.write(content['content'].encode())

        sioemit("uploadImageResult", resp, flask.session["channel"])
        
        resp = socksend(users[flask.session["uuid"]], content)

        uploadFilePath = uploadFileRoot + resp['filename']
        
        with open(uploadFilePath, 'rb') as f:
            resp['content'] = f.read().decode()

        if b"sendtome" in content:
            sendtome_flag = True
        else:
            sendtome_flag = False

        print(f"/!!!!!!!here!!!!!/ {resp}")

        if sendtome_flag:
            sioemit("newchat", resp, users[content['to']])
        else:
            sioemit("newchat", resp, users[content['to']])
            sioemit("newchat", resp, users[content['from']])

    except:
        print(f"/!!!!!!!here!!!!!/ {resp}")
        resp = f'[x] upload "{uploadFilePath}" error'

        sioemit("uploadImageResult", resp, flask.session["channel"])


@socket_io.on("chatsend")
def chatsend(content):
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))

    try:
        if type(content) != dict:
            content = content.encode('latin-1')
            content = json.loads(content)

        if content["from"] != flask.session["userid"]:
            print(f"[x] {content['from']} != {flask.session['userid']}")
            return "[x] request from user is different from session"

    except Exception as e:
        logging.error(traceback.format_exc())
        pass

    if b"sendtome" in content:
        sendtome_flag = True
    else:
        sendtome_flag = False

    resp = socksend(users[flask.session["uuid"]], content)

    if type(resp) != dict:
        resp = {"result": 0, "msg":resp}
    else:
        resp = {"result": 1, "msg":resp}
    
    try:
        if sendtome_flag:
            sioemit("newchat", resp, users[flask.session["userid"]])
        else:
            sioemit("newchat", resp, users[resp["msg"]["to"]])
            sioemit("newchat", resp, users[resp["msg"]["from"]])
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