#-*- coding: cp949 -*-
import socketserver
import pymysql
import threading
import json, re
import logging, traceback
logging.basicConfig(level=logging.ERROR)

lock = threading.Lock()
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
			print(req[key])
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
		if len(req['userid'])>50 or len(req['userpw'])>50:
			return "toolong"
		if self.duplicatedCheck(req) != ():
			return "duplicated"

		query = f"insert into user values(null, '{req['userid']}', '{req['userpw']}', '{req['uploadFilePath']}')"
		print(f"[+] query(register) - {query}")
		self.cursor.execute(query)
		self.conn.commit()
		
		result = self.duplicatedCheck(req)
		if result:
			return True
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
						if r == "duplicated":
							self.request.sendall(b"[x] duplicated id")
						elif r == "toolong":
							self.request.sendall(b"[x] parameter too long")
						else:
							self.request.sendall(b"true")
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
