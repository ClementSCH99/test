# main_threaded.py

import threading
import queue
import time

from collections import deque

from LabJackU6 import LabJackU6Controller
from DataLogger import DataLogger
from controllers.brake_bench import BrakeBenchController
from threads.acquisition import loop_acquisition
from threads.saving import loop_logging
from threads.plotting import loop_plotting
from threads.hmi import loop_hmi


def main():
	
	# Time start snapshot
	start_t = time.time()

	# Object instantiation
	lj = LabJackU6Controller(
		log_dir = "logs/",
		log_file = "LabJackU6_Test.log"
	)
	
	dl = DataLogger(
		save_file = "BrakeTest_02.csv",
		autosave_interval = 300,
		autosave_file = "BrakeTest_autosave_02.csv"
		)
		
	ctrl = BrakeBenchController(
		target_up = -111,	#Newton
		target_down = -5,	#Newton
		max_cycles = 50000,
		rest_time = 0.35
		)

	# LoadCell initialisation
	lj.add_loadcell(
		name = "LC0",
		ain_pos = "AIN0",
		ain_neg = "AIN1",
		exc = 5.0,
		rated_F = 2224.91,	#Newtons (Load cell is 500lbs = 22224.81N)
		mVperV = 0.003,
		gain_idx = 3
		)
	lj.tare_loadcell("LC0")

	# Data Queue & Buffer
	data_q = queue.Queue()
	plot_q = queue.Queue()

	# Thread Events
	running = threading.Event()
	save_event = threading.Event()
	running.set()

	# Threads Definition
	acq_th = threading.Thread(
		target = loop_acquisition,
		args = (lj, ctrl, data_q, plot_q, running, start_t, 0.05),
		daemon = True
		)

	log_th = threading.Thread(
		target = loop_logging,
		args = (dl, data_q, running, save_event),
		daemon = True
		)
	
	plt_th = threading.Thread(
		target = loop_plotting,
		args = (plot_q, running, 300),
		daemon = True
		)
	
	hmi_th = threading.Thread(
		target = loop_hmi,
		args = (ctrl, running, 1.0),
		daemon = True
		)

	# Strating Threads
	hmi_th.start()
	acq_th.start()
	log_th.start()
	plt_th.start()
	print("Threads started. Press CTRL+C to stop.")
	

	# Main loop
	try:
		while ctrl.phase != "end_of_test":
			time.sleep(0.1)

	except KeyboardInterrupt:
		print("\nKeyboard interrupt. Stopping ...")

	finally:
		running.clear()
		#save_event.set()
		
		hmi_th.join()
		acq_th.join()
		log_th.join()
		plt_th.join()
		
		lj.close(1)


if __name__ == "__main__":
	main()
