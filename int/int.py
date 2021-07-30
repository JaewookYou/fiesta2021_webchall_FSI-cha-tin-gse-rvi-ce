#-*- coding: latin-1 -*-
import socketserver
import pymysql
import threading
from arang import *

lock = threading.Lock()

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
	def setup(self):
		print('{}:{} connected'.format(*self.client_address))
		
	def handle(self):
		while 1:
			self.data = self.request.recv(4096).strip()
			print(self.client_address[0])
			print(self.data)
			if not self.data:
				break
			self.request.sendall(self.data)

	def finish(self):
		print('{}:{} disconnected'.format(*self.client_address))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
	pass

if __name__ == "__main__":
	HOST, PORT = "0.0.0.0", 9091
	server = ThreadedTCPServer((HOST,PORT), ThreadedTCPRequestHandler)
	#server = socketserver.TCPServer((HOST, PORT), TCPHandler)

	server.serve_forever()

# import socket
# import os
# from _thread import *

# ServerSideSocket = socket.socket()
# host = '127.0.0.1'
# port = 9091
# ThreadCount = 0
# try:
#     ServerSideSocket.bind((host, port))
# except socket.error as e:
#     print(str(e))

# print('Socket is listening..')
# ServerSideSocket.listen(5)

# def multi_threaded_client(connection):
#     while True:
#     	r = ''
#         data = connection.recv(4096).strip()
#         print(data)
#         r = data
#         if not data:
#             break
#         connection.sendall(r)
#     connection.close()

# while True:
#     Client, address = ServerSideSocket.accept()
#     print('Connected to: ' + address[0] + ':' + str(address[1]))
#     start_new_thread(multi_threaded_client, (Client, ))
#     ThreadCount += 1
#     print('Thread Number: ' + str(ThreadCount))

# ServerSideSocket.close()

