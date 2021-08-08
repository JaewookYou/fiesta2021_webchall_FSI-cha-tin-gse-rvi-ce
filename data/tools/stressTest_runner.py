#-*- coding: utf-8 -*-
from arang import *
import os
import logging, traceback
import concurrent.futures 
import subprocess
import sys
from threading import Lock
logging.basicConfig(level=logging.ERROR)

def target(x):
	try:
		p = subprocess.run(['python3', 'stressTest.py', f'{x}'], stdout=sys.stdout, stderr=sys.stderr, timeout=5)
	except subprocess.TimeoutExpired:
		pass

	return x

def go():
	cnt = 1
	workers = 32
	
	with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
		try:
			futures = {executor.submit(target, x):x for x in range(0,workers)}
		except KeyboardInterrupt:
			quit=True
		for future in concurrent.futures.as_completed(futures):
			try:
				data = future.result()
			except Exception as e:
				print(f"[x] err.. {str(e)}")
				logging.error(traceback.format_exc())
			else:
				print(f"[+] {cnt} / {workers} : {data}")
				cnt += 1



if __name__ == "__main__":
	while 1:
		go()