# threads/logging.py

import traceback
import time
from queue import Empty

def loop_logging(dl, data_q, running, save_event):
	"""Threads to log data from data_q"""
	
	try:
		while running.is_set() or not data_q.empty():
			
			try:
				
				# Get data from data_q
				data = data_q.get(block = True, timeout = 0.1)
				
				# Reccord parsed data
				dl.log(data)
			
			except Empty:
				pass
		
		# Manual seve event
		if save_event.is_set():
			dl.save_csv()
			pass
	
	except Exception as e:
		print(f"Error in logging thread: {e}")
		traceback.print_exc()
		time.sleep(0.01)
		
	finally:
		print("Final save before exit...")
		dl.save_csv()
