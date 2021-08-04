#-*- coding: cp949 -*-
import socketserver
import pymysql
import threading
import json, re, base64, os
import logging, traceback
logging.basicConfig(level=logging.ERROR)

lock = threading.Lock()

def secureFileName(filename):
    filteringList = ["..","\\","\x00","'",'"']
    for filterChar in filteringList:
        filename = filename.replace(filterChar, "")
    return filename

class mysqlapi:
	def __init__(self):
		self.conn = pymysql.connect(
			user = 'arangtest',
			passwd = 'testpass',
			host = 'arang.kr',
			db = 'chatdb',
			charset = 'utf8'
		)
		self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)

	def safeQuery(self, req):
		for key in req.keys():
			req[key] = re.sub(r"[\'\"\\\(\)\|\&\[\]\!\@\#\$\%]",r'\\\g<0>', req[key])
		return req

	def doLogin(self, req):
		req = self.safeQuery(req)
		query = f"select userid from chatdb.user where userid='{req['userid']}' and userpw='{req['userpw']}'"
		print(f"[+] query(login) - {query}")
		self.cursor.execute(query)
		result = self.cursor.fetchall()
		print(f"[+] result(login) - {result}")
		return result

	def duplicatedCheck(self, req):
		req = self.safeQuery(req)
		query = f"select userid from chatdb.user where userid='{req['userid']}'"
		print(f"[+] query(dupchk) - {query}")
		self.cursor.execute(query)
		result = self.cursor.fetchall()
		print(f"[+] result(dupchk) - {result}")
		return result

	def doRegister(self, req):
		req = self.safeQuery(req)		
		if self.duplicatedCheck(req) != ():
			return "[x] duplicated id"

		try:
			uploadFilePath = ""
			uploadFileRoot = f"./uploads/{req['userid']}/"
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

			resp = f"[+] upload {uploadFilePath} success!"
			
		except:
			logging.error(traceback.format_exc())
			resp = f'[x] upload "{uploadFilePath}" error'
			

		query = f"insert into user values(null, '{req['userid']}', '{req['userpw']}', '{filename}')"
		print(f"[+] query(register) - {query}")
		self.cursor.execute(query)
		self.conn.commit()
		
		if self.duplicatedCheck(req):
			return resp
		else:
			return False


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
			self.data = self.request.recv(4096).strip().decode()
			
			print(self.client_address[0])
			if not self.data:
				break
			try:
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
				else:
					self.request.sendall(b"[x] please input right command")
				
			except:
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
