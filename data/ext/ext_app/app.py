#-*- coding: latin-1 -*-
### this is external server's app.py
### and below is the first flag
### fiesta{ok_y0u_g0t_the_ext_server's_code!_lets_dig_the_2nd_flag!}
import flask_socketio
import flask
import datetime, uuid, socket, json, threading, os, base64, re, time, signal, errno
from functools import wraps
import logging, traceback
logging.basicConfig(level=logging.INFO)
logging.getLogger('werkzeug').setLevel(level=logging.WARNING)


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
    if "uuid" not in flask.session:
        flask.session["uuid"] = str(uuid.uuid1())

    if flask.session["uuid"] not in users:
        flask.session["host"] = ("172.22.0.4",9091)
        logging.info(f"[+] new socket conn {flask.session['uuid']}")
        users[flask.session["uuid"]] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        users[flask.session["uuid"]].connect(flask.session["host"])

    if loginCheck:
        if "isLogin" not in flask.session:
            return False
        else:
            return True

    if "isLogin" in flask.session:
        return True
    
    return False

def sockError(e):
    if "errcnt" not in flask.session:
        flask.session["errcnt"] = 1

    logging.info(f"[+] ext sock resend {flask.session['errcnt']} : {str(e)}")

    if flask.session["errcnt"] < 3:
        flask.session["errcnt"] += 1
        return False
    elif flask.session["errcnt"] >= 3:
        users[flask.session["uuid"]].close()
        users.pop(flask.session['uuid'])
        flask.session.pop('errcnt', False)
        sessionCheck()
        logging.error('[x] sock resend max try exceed')
        return '[x] sock resend max try exceed'

def socksend(sock, content):
    if "errcnt" in flask.session:
        if flask.session["errcnt"] >= 3:
            users[flask.session["uuid"]].close()
            users.pop(flask.session['uuid'])
            flask.session.pop('errcnt', False)
            logging.error('[x] sock resend max try exceed, try again plz')
            sessionCheck()
            return '[x] sock resend max try exceed, try again plz'

    if type(content) == dict:
        content = json.dumps(content).encode()+b"\n"
    
    logging.info(f"[+] ext sock send - {sock} : {content}")
    r=""

    try:
        with block:
            sock.send(content)
            sock.settimeout(2)
            r = sock.recv(900000).decode('latin-1')
            return json.loads(r)
    except BrokenPipeError as e:
        if sockError(e):
            return '[x] sock resend max try exceed, plz try again'
        if flask.session["uuid"] in users and flask.session["errcnt"] < 3:
            return socksend(users[flask.session["uuid"]], content)
    except OSError as e:
        if sockError(e):
            return '[x] sock resend max try exceed, plz try again'
        if flask.session["uuid"] in users and flask.session["errcnt"] < 3:
            return socksend(users[flask.session["uuid"]], content)
    except socket.timeout:
        if sockError(e):
            return '[x] sock resend max try exceed, plz try again'
        if flask.session["uuid"] in users and flask.session["errcnt"] < 3:
            return socksend(users[flask.session["uuid"]], content)
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


@app.route("/logout")
def logout():
    flask.session.pop('isLogin', False)
    if "uuid" in flask.session:
        if flask.session["uuid"] in users:
            users[flask.session["uuid"]].close()
            users.pop(flask.session['uuid'])
            logging.info(f"logout {users[flask.session['uuid']]}")
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
        
        if "msg" in flask.request.args:
            msg = flask.request.args["msg"]
        else:
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
            return flask.render_template("login.html", msg=queryResult)

    
@app.route("/register", methods=["GET","POST"])
def register():
    if flask.request.method == "GET":
        if sessionCheck(loginCheck=True):
            return flask.redirect(flask.url_for("chat"))
        
        if "msg" in flask.request.args:
            msg = flask.request.args["msg"]
        else:
            msg = "false"

        return flask.render_template("register.html", msg=msg)
    else:
        if sessionCheck():
            return flask.redirect(flask.url_for("chat"))

        if not checkUserIDPW(flask.request.form["userid"], flask.request.form["userpw"]):
            return flask.render_template("register.html", msg="invalid userid or userpw")

        profileImageFile = flask.request.files["profileImage"]
        if profileImageFile.filename == "":
            resp = "[x] please attach a profile image"
            return flask.render_template("register.html", msg=resp)
        
        fileContent = base64.b64encode(profileImageFile.read())
        if len(fileContent) > 16384:
            resp = "[x] profile image too big. under 1.6k plz"
            return flask.render_template("register.html", msg=resp)
            
        if type(fileContent) == bytes:
            fileContent = fileContent.decode()
        resp = doRegisterQuery(
            users[flask.session["uuid"]], 
            flask.request.form["userid"], 
            flask.request.form["userpw"], 
            profileImageFile.filename,
            fileContent 
        )

        return flask.render_template("login.html", msg=resp)

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
    if 'content' not in r:
        r = 'x'
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

    if content["from"] != flask.session["userid"]:
        logging.info(f"[x] getlist {content['from']} != {flask.session['userid']}")
        resp = "[x] request from user is different from session"
        sioemit("getlist", resp, users[flask.session["userid"]])
        return

    resp = socksend(users[flask.session["uuid"]], content)

    sioemit("getlist", resp, users[flask.session["userid"]])

@socket_io.on("getchatmsg")
def getchatmsg(content):
    if not sessionCheck(loginCheck=True):
        resp = "[x] please login"
        sioemit("getchatmsg", resp, flask.session["channel"])
        return

    if content["from"] != flask.session["userid"]:
        logging.info(f"[x] getchatmsg {content['from']} != {flask.session['userid']}")
        resp = "[x] request from user is different from session"
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

    if content["from"] != flask.session["userid"]:
        logging.info(f"[x] roomadd {content['from']} != {flask.session['userid']}")
        resp = "[x] request from user is different from session"
        sioemit("roomadd", resp, flask.session["channel"])
        return

    resp = socksend(users[flask.session["uuid"]], content)

    if 'msg' in resp:
        sioemit("roomadd", resp, flask.session["channel"])
        if resp["to"] in users:   
            sioemit("newchat", resp, users[resp["to"]])
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
        logging.info(f"[x] imagesend {content['from']} != {flask.session['userid']}")
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
        logging.info(f"[+] upload image - {uploadFilePath}")
    except:
        resp = f'[x] upload "{uploadFilePath}" error'
        logging.info(resp)
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

    if "sendtome" in content:
        sendtome_flag = True
    else:
        sendtome_flag = False

    try:
        if type(content) != dict:
            content = content.encode('latin-1')
            content = json.loads(content)

        if content["from"] != flask.session["userid"]:
            logging.info(f"[x] chatsend {content['from']} != {flask.session['userid']}")
            return "[x] request from user is different from session"

        if content["msg"] == "":
            return "[x] blank content. please input content"

    except Exception as e:
        pass

    resp = socksend(users[flask.session["uuid"]], content)

    if sendtome_flag:
        sioemit("newchat", resp, users[flask.session["userid"]])
    else:
        sioemit("newchat", resp, users[resp["to"]])
        sioemit("newchat", resp, users[resp["from"]])

    if 'msg' in resp:
        logging.info(f"[+] newchat - {resp['from']} -> {resp['to']} : {resp['msg']}")
    


@socket_io.on("connect")
def connected():
    logging.info("connected")

@socket_io.on("disconnect")
def disconnected():
    logging.info("disconnected")
    if "uuid" in flask.session:
        if flask.session["uuid"] in users:
            users[flask.session["uuid"]].close()
            users.pop(flask.session['uuid'])
            logging.info(f"disconnect {users[flask.session['uuid']]}")


if __name__ == "__main__":
    try:
        socket_io.run(app, host="0.0.0.0", port=9090)
    except Exception as ex:
        pass
