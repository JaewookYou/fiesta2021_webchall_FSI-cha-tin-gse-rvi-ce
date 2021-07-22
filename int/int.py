#-*- coding: latin-1 -*-
import socketserver
import pymysql
import threading
from arang import *

lock = threading.Lock()

class TCPHandler(socketserver.BaseRequestHandler):
	def setup(self):
		print('{}:{} connected'.format(*self.client_address))
		
	def handle(self):
		while 1:
			self.data = self.request.recv(1024).strip()
			print(self.client_address[0])
			print(self.data)
			if not self.data:
				break
			self.request.sendall(self.data)

	def finish(self):
		print('{}:{} disconnected'.format(*self.client_address))




class chatServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
	pass

if __name__ == "__main__":
	HOST, PORT = "0.0.0.0", 9091
	server = chatServer((HOST,PORT), TCPHandler)
	#server = socketserver.TCPServer((HOST, PORT), TCPHandler)

	server.serve_forever()