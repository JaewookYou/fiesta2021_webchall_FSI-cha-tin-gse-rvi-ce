#-*- coding: latin-1 -*-
### this is external server's app.py
import flask_socketio
import flask
import datetime, uuid, socket, json, threading, os, base64, re
import logging, traceback
import ssl
logging.basicConfig(level=logging.ERROR)

app = flask.Flask(__name__)
app.secret_key = os.urandom(16)
app.config['MAX_CONTENT_LENGTH'] = 80 * 1024 * 1024
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
        flask.session["host"] = ("172.22.0.4",9091)
        print(f"[+] new socket conn {flask.session['uuid']}")
        users[flask.session["uuid"]] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        users[flask.session["uuid"]].connect(flask.session["host"])

    return False


def socksend(sock, content):
    if type(content) == dict:
        content = json.dumps(content).encode()+b"\n"
    r=""
    try:
        with block:
            print(f"[+] ext sock send {content}")
            sock.send(content)
            r = sock.recv(900000).decode('latin-1')
            print(f"[+] ext sock recv {r}")
            return json.loads(r)
    except BrokenPipeError as e:
        print(f"[+] ext sock resend {str(e)}")
        users[flask.session["uuid"]] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
        users[flask.session["uuid"]].connect(flask.session["host"])
        return socksend(users[flask.session["uuid"]], content)
    except OSError:
        print(f"[+] ext sock resend(oserror)")
        users[flask.session["uuid"]] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
        users[flask.session["uuid"]].connect(flask.session["host"])
        return socksend(users[flask.session["uuid"]], content)
    except:
        logging.error(traceback.format_exc())
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
        print(f"[+]ext login query result {queryResult}")
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
        if len(fileContent) > 16384:
            resp = "[x] profile image too big. under 1.6k plz"
            return flask.redirect(flask.url_for("login", msg=resp))
            
        if type(fileContent) == bytes:
            fileContent = fileContent.decode()

        resp = doRegisterQuery(
            users[flask.session["uuid"]], 
            flask.request.form["userid"], 
            flask.request.form["userpw"], 
            profileImageFile.filename,
            fileContent 
        )
        if "[+] register success" == resp:
            resp = "false"
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
            flask.session["host"] = (t[0], int(t[1]))
            
            users[flask.session["uuid"]] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
            users[flask.session["uuid"]].connect(flask.session["host"])

        flask.session["channel"] = channel
        flask_socketio.join_room(channel)

        sioemit("join",{"result":"success"}, channel)
    else:
        sioemit("join",{"result":"fail"}, channel)

@socket_io.on("getlist")
def getlist(content):
    if not sessionCheck(loginCheck=True):
        resp = "[x] please login"
        sioemit("getlist", resp, flask.session["channel"])
        return

    try:
        if type(content) != dict:
            content = content.encode('latin-1')
            content = json.loads(content)
        if content["from"] != flask.session["userid"]:
            print(f"[x] {content['from']} != {flask.session['userid']}")
            resp = "[x] request from user is different from session"
            sioemit("getlist", resp, users[flask.session["userid"]])
            return
    except Exception as e:
        pass

    resp = socksend(users[flask.session["uuid"]], content)

    sioemit("getlist", resp, users[flask.session["userid"]])

@socket_io.on("getchatmsg")
def getchatmsg(content):
    if not sessionCheck(loginCheck=True):
        resp = "[x] please login"
        sioemit("getchatmsg", resp, flask.session["channel"])
        return

    try:
        if type(content) != dict:
            content = content.encode('latin-1')
            content = json.loads(content)
        if content["from"] != flask.session["userid"]:
            print(f"[x] {content['from']} != {flask.session['userid']}")
            resp = "[x] request from user is different from session"
            sioemit("getchatmsg", resp, flask.session["channel"])
            return
    except Exception as e:
        resp = "[x] error with verifying data/user"
        sioemit("getchatmsg", resp, flask.session["channel"])
        return

    resp = socksend(users[flask.session["uuid"]], content)

    new_resp = []
    for i in resp:
        if i['isImage'] == True:
            uploadFileRoot = f"{os.path.abspath('./')}/uploads/{i['chatfrom']}/"
            uploadFilePath = uploadFileRoot + i['chatmsg']
            try:
                with open(uploadFilePath, 'rb') as f:
                    i['content'] = f.read().decode()
            except:
                i['content'] = "x"

        new_resp.append(i)

    sioemit("getchatmsg", resp, users[flask.session["userid"]])

@socket_io.on("roomadd")
def roomadd(content):
    if not sessionCheck(loginCheck=True):
        resp = "[x] please login"
        sioemit("roomadd", resp, flask.session["channel"])
        return

    try:
        if type(content) != dict:
            content = content.encode('latin-1')
            content = json.loads(content)
        if content["from"] != flask.session["userid"]:
            print(f"[x] {content['from']} != {flask.session['userid']}")
            resp = "[x] request from user is different from session"
            sioemit("roomadd", resp, flask.session["channel"])
            return
    except Exception as e:
        resp = "[x] error with verifying data/user"
        sioemit("roomadd", resp, flask.session["channel"])
        return

    resp = socksend(users[flask.session["uuid"]], content)

    if 'msg' in resp:
        sioemit("roomadd", resp, flask.session["channel"])

        if type(resp) != dict:
            resp = {"result": 0, "msg":resp}
        else:
            resp = {"result": 1, "msg":resp}
        
        sioemit("newchat", resp, users[resp["msg"]["to"]])
    else:
        sioemit("roomadd", resp, flask.session["channel"])



@socket_io.on("imagesend")
def imagesend(content):        
    if not sessionCheck(loginCheck=True):
        resp = "[x] please login"
        sioemit("uploadImageResult", resp, flask.session["channel"])
        return

    resp = ""

    if content["from"] != flask.session["userid"]:
        print(f"[x] {content['from']} != {flask.session['userid']}")
        resp = "[x] request from user is different from session"
        sioemit("uploadImageResult", resp, flask.session["channel"])
        return

    uploadPath = ""
    uploadFileRoot = f"{os.path.abspath('./')}/uploads/{content['from']}/"
    if not os.path.exists(uploadFileRoot) and not os.path.isdir(uploadFileRoot):
        os.makedirs(uploadFileRoot)

    content['filename'] = secureFileName(content['filename'])
    
    if content['filename'] == "":
        resp = f"[x] please attach a image"
        sioemit("uploadImageResult", resp, flask.session["channel"])
        return

    uploadFilePath = uploadFileRoot + content['filename']

    try:
        with open(uploadFilePath, 'wb') as f:
            f.write(content['content'].encode())
        content.pop('content')
    except:
        logging.error(traceback.format_exc())
        resp = f'[x] upload "{uploadFilePath}" error'
        sioemit("uploadImageResult", resp, flask.session["channel"])
        
    resp = socksend(users[flask.session["uuid"]], content)

    if b"sendtome" in content:
        sendtome_flag = True
    else:
        sendtome_flag = False

    sioemit("uploadImageResult", resp, flask.session["channel"])

    if sendtome_flag:
        sioemit("uploadImageResult", resp, users[content['to']])
    else:
        sioemit("uploadImageResult", resp, users[content['to']])
        sioemit("uploadImageResult", resp, users[content['from']])


@socket_io.on("chatsend")
def chatsend(content):
    if not sessionCheck(loginCheck=True):
        resp = "[x] please login"
        sioemit("newchat", resp, flask.session["channel"])
        return

    try:
        if type(content) != dict:
            content = content.encode('latin-1')
            content = json.loads(content)

        if content["from"] != flask.session["userid"]:
            print(f"[x] {content['from']} != {flask.session['userid']}")
            return "[x] request from user is different from session"

        if content["msg"] == "":
            return "[x] blank content. please input content"

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
    users[flask.session["uuid"]].close()
    print(users[flask.session["uuid"]])


if __name__ == "__main__":
    try:
        socket_io.run(app, host="0.0.0.0", debug=True, port=9090)
    except Exception as ex:
        print(ex)
