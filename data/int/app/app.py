#-*- coding: cp949 -*-
### this is internal server's app.py
import socketserver
import pymysql
import threading
import json, re, base64, os, datetime, time
import logging, traceback
logging.basicConfig(level=logging.ERROR)

lock = threading.Lock()

def secureFileName(filename):
    filteringList = ["..","\\","\x00","'",'"']
    for filterChar in filteringList:
        filename = filename.replace(filterChar, "")
    return filename

def whatTimeIsIt():
	return datetime.datetime.strftime(datetime.datetime.now(),"%Y-%m-%d %H:%M:%S")

class mysqlapi:
	def __init__(self):
		self.conn = pymysql.connect(
			user = 'chatdb_admin',
			passwd = 'th1s_1s_ch4tdb_4dm1n_p4ssw0rd',
			host = '172.22.0.5',
			db = 'chatdb',
			charset = 'utf8'
		)
		self.conn.autocommit(True)
		self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)

	def safeQuery(self, req):
		for key in req.keys():
			req[key] = re.sub(r"[\'\"\\\(\)\|\&\[\]\!\@\#\$\%]",r'\\\g<0>', req[key])
		return req

	def duplicatedCheck(self, req):
		req = self.safeQuery(req)
		query = f"select userid from chatdb.user where userid='{req['userid']}'"
		print(f"[+] query(dupchk) - {query}")
		self.cursor.execute(query)
		result = self.cursor.fetchall()
		print(f"[+] result(dupchk) - {result}")
		
		if result != ():
			return True
		else:
			return False


	def doLogin(self, req):
		req = self.safeQuery(req)
		query = f"select userid from chatdb.user where userid='{req['userid']}' and userpw='{req['userpw']}'"
		print(f"[+] query(login) - {query}")
		self.cursor.execute(query)
		result = self.cursor.fetchall()
		print(f"[+] result(login) - {result}")
		return result

	def doRegister(self, req):
		req = self.safeQuery(req)		
		if self.duplicatedCheck(req):
			return "[x] duplicated id"

		try:
			uploadFilePath = ""
			uploadFileRoot = f"{os.path.abspath('./')}/uploads/{req['userid']}/"
			if not os.path.exists(uploadFileRoot) and not os.path.isdir(uploadFileRoot):
				os.makedirs(uploadFileRoot)
			filename = secureFileName(req['filename'])
			uploadFilePath = uploadFileRoot + filename
			
			print(f"[+] upload path - {uploadFilePath}")
			
			cont = base64.b64decode(req['profileImageContent'])
			if type(cont) == str:
				cont = cont.encode()

			with open(uploadFilePath,"wb") as f:
				f.write(cont)

			resp = "[+] register success"
			
		except:
			logging.error(traceback.format_exc())
			resp = f'[x] upload "{uploadFilePath}" error'
			

		query = f"insert into user (userid, userpw, userProfileImagePath) values('{req['userid']}', '{req['userpw']}', '{filename}')"
		print(f"[+] query(register) - {query}")
		self.cursor.execute(query)
		self.conn.commit()
		
		if self.duplicatedCheck(req):
			return resp
		else:
			return False


	def getChatRoom(self, req):
		query = f"select roomseq from chatroom where (user_a='{req['from']}' and user_b='{req['to']}') or (user_a='{req['to']}' and user_b='{req['from']}')"
		print(f"[+] query(getChatRoom) - {query}")
		self.cursor.execute(query)
		result = self.cursor.fetchall()
		print(f"[+] result(getChatRoom) - {result}")
		if result != ():
			return result
		else:
			return False

	def createChatRoom(self, req):
		query = f"insert into chatroom (user_a, user_b, lastmsg, lastdate) values('{req['from']}', '{req['to']}', null, null)"
		print(f"[+] query(createChatRoom) - {query}")
		self.cursor.execute(query)
		self.conn.commit()
		if self.getChatRoom(req) != ():
			return True
		else:
			return False

	def updateRecentChat(self, req):
		query = f"update chatroom set lastmsg='{req['msg'][:30]}', lastdate='{req['date']}' where (user_a='{req['from']}' and user_b='{req['to']}') or (user_a='{req['to']}' and user_b='{req['from']}')"
		print(f"[+] query(updateRecentChat) - {query}")
		self.cursor.execute(query)
		self.conn.commit()

	def insertChat(self, req, isImage=False):
		query = f"insert into chat (chatfrom, chatto, chatmsg, chatdate{', isImage' if isImage else ''}) values('{req['from']}', '{req['to']}', '{req['msg']}', '{req['date']}'{', true' if isImage else ''})"
		print(f"[+] insertChat query - {query}")
		self.cursor.execute(query)
		self.conn.commit()

	def doSaveChatdata(self, req):
		req = self.safeQuery(req)
		req['date'] = whatTimeIsIt()
		
		chatroomNum = self.getChatRoom(req)
		if not chatroomNum:
			if not self.createChatRoom(req):
				return "[x] create chat room error"

		self.updateRecentChat(req)

		self.insertChat(req)

		return req

	def imagesend(self, req):
		req = self.safeQuery(req)
		req['date'] = whatTimeIsIt()
		req['msg'] = req['filename']
		
		print(req)
		
		chatroomNum = self.getChatRoom(req)
		if not chatroomNum:
			if not self.createChatRoom(req):
				return "[x] create chat room error"

		self.updateRecentChat(req)		
		self.insertChat(req, isImage=True)

		req['isImage'] = True

		return req
		

	def getChatMsg(self, req):
		req = self.safeQuery(req)

		query = f"select * from chat where (chatfrom='{req['from']}' and chatto='{req['to']}') or (chatfrom='{req['to']}' and chatto='{req['from']}') order by 1 desc limit 0, 30"
		
		self.cursor.execute(query)
		result = self.cursor.fetchall()
		
		if result != ():
			r = []
			for i in result:
				i['chatdate'] = str(i['chatdate'])
				r.append(i)
			return r[::-1]
		else:
			return False

	def getProfileImage(self, req):
		req = self.safeQuery(req)

		query = f"select userProfileImagePath from user where userid='{req['userid']}'"
		print(f"[+] query(getChatMsg) - {query}")
		self.cursor.execute(query)
		result = self.cursor.fetchall()
		print(f"[+] result(getChatMsg) - {result}")
		if result != ():
			uploadFileRoot = f"{os.path.abspath('./')}/uploads/{req['userid']}/"
			uploadFilePath = f"{uploadFileRoot}{result[0]['userProfileImagePath']}"
			with open(uploadFilePath, 'rb') as f:
				cont = f.read()

			convertedContent = f"data:image/png;base64,{base64.b64encode(cont).decode()}"
			return convertedContent

		else:
			return False

	def getlist(self, req):
		req = self.safeQuery(req)
		query = f"select * from chatroom where user_a='{req['from']}' or user_b='{req['from']}' order by lastdate desc"
		print(f"[+] query(getChatMsg) - {query}")
		self.cursor.execute(query)
		result = self.cursor.fetchall()
		print(f"[+] result(getChatMsg) - {result}")
		if result != ():
			r = []
			for i in result:
				i['lastdate'] = str(i['lastdate'])
				r.append(i)
			return r
		else:
			return False

	def roomadd(self, req):
		req = self.safeQuery(req)
		req['userid'] = req['to']
		if not self.duplicatedCheck(req):
			return f"[x] there has no id - {req['to']}"

		req['date'] = whatTimeIsIt()
		
		chatroomNum = self.getChatRoom(req)
		if not chatroomNum:
			if not self.createChatRoom(req):
				return "[x] create chat room error"
			else:
				if req['to'] == "welcomebot":
					req['msg'] = "Hello! This is our first chat! Welcome to FSI Chat"
				else:
					req['msg'] = f"{req['from']} make room with {req['to']}! check this"
				
				self.updateRecentChat(req)

				self.insertChat(req)
				return req
		else:
			return "[x] already have room error"



class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
	def setup(self):
		print('{}:{} connected'.format(*self.client_address))
		
	def handle(self):
		try:
			self.is_mysql_connected
		except:
			self.mysqlapi = mysqlapi()
			self.is_mysql_connected= True

		while 1:
			self.data = self.request.recv(900000).strip().decode()

			print(self.client_address[0])
			if not self.data:
				break
			try:
				with lock:
					req = json.loads(self.data)
					cmd = req["command"]

					if cmd == "login":
						r = self.mysqlapi.doLogin(req)
						if r:
							self.request.sendall(json.dumps(r[0]).encode())
						else:
							self.request.sendall(b"[x] id/pw is not correct")

					elif cmd == "register":
						r = self.mysqlapi.doRegister(req)
						if r:
							self.request.sendall(r.encode())
						else:
							self.request.sendall(b"[x] register fail")
							
					elif cmd == "chatsend":
						r = self.mysqlapi.doSaveChatdata(req)
						if r:
							self.request.sendall(json.dumps(r).encode())
						else:
							self.request.sendall(b"[x] chat send fail")

					elif cmd == "getchatmsg":
						r = self.mysqlapi.getChatMsg(req)
						if r:
							self.request.sendall(json.dumps(r).encode())
						else:
							self.request.sendall(b"[x] get chat msg fail")

					elif cmd == "getProfileImage":
						r = self.mysqlapi.getProfileImage(req)
						if r:
							self.request.sendall(r.encode())
						else:
							self.request.sendall(b"x")

					elif cmd == "imagesend":
						r = self.mysqlapi.imagesend(req)
						if r:
							self.request.sendall(json.dumps(r).encode())
						else:
							self.request.sendall(b"[x] sending image fail")

					elif cmd == "getlist":
						r = self.mysqlapi.getlist(req)
						if r:
							self.request.sendall(json.dumps(r).encode())
						else:
							self.request.sendall(b"[x] getlist fail")

					elif cmd == "roomadd":
						r = self.mysqlapi.roomadd(req)
						if r:
							self.request.sendall(json.dumps(r).encode())
						else:
							self.request.sendall(b"[x] roomadd fail")


					else:
						self.request.sendall(b"[x] please input right command")
				
			except:
				print(self.data)
				logging.error(traceback.format_exc())
				self.request.sendall(b"[x] internal server error - exception")

	def finish(self):
		print('{}:{} disconnected'.format(*self.client_address))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
	pass

if __name__ == "__main__":
	HOST, PORT = "0.0.0.0", 9091
	server = ThreadedTCPServer((HOST,PORT), ThreadedTCPRequestHandler)
	server.serve_forever()
