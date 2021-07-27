#-*- coding: utf-8 -*-
from arang import *
import os, datetime, sys
import socketio

u = f"http://127.0.0.1:9090/login?id={hexencode(os.urandom(16)).decode()}"
s = requests.session()

r = s.get(u)

h = r.headers
headers = {}
hs = h["Set-Cookie"].split(",")

for i in hs:
	if ";" in i:
		i = i.split(";")[0]
	t = i.split('=')
	k = t[0].strip()
	v = t[1].strip()
	headers[k] = v

loginid = headers["loginid"]
uuid = headers["uuid"]
session = headers["session"]

print(f"[+] headers - {headers}")

sio = socketio.Client()
sio.connect('http://localhost:9090/')

joinflag = False

@sio.on('join')
def join(data):
	global joinflag
	print(f"[+] join : {loginid}-{uuid} {data}")
	if data["result"] == "fail":
		print("[x] join room fail")
	else:
		joinflag = True

@sio.on('newchat')
def newchat(data):
	if data["result"] == 0:
		print(f"[x] err... {data['msg']}")
	elif data["result"] == 1:
		print(f"[+] newchat {data['from']}->{data['to']} : {data['msg']}")

datas = {"channel":uuid, "loginid":loginid}
sio.emit("join", datas)

cnt = 0
while 1:
	if joinflag:
		date = datetime.datetime.strftime(datetime.datetime.now(),"%Y-%m-%d %H:%M:%S")
		data = {"date":date,"from":loginid, "to":"admin", "msg":f"hahaasdfahahaasdfahahaas{date}"}
		sio.emit("chatsend", data)
		time.sleep(0.1)
	else:
		time.sleep(1)

	cnt += 1

	if cnt > 3:
		print(f"[+] end")
		sio.disconnect()
		sys.exit()



