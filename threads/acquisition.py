# threads/acquisition.py

import time
import traceback

def loop_acquisition(lj, controller, data_q, plot_q, running, start_t, interval):
	"""
	Acquisition thread. Reponsible of:
	- Reading and storing inputs dict
	- Applling outputs dict to hardware
	- Pushing PINs state in a data_q
	- Puhsing reduces PINs state in a plot_q
	"""
	
	inputs_list = controller.required_inputs
	next_sleep = time.time()
	
	while running.is_set():
		try:
			timestamp = time.time() - start_t
			
			inputs = {}
			
			# Update inputs
			for ipt in inputs_list:
				if ipt.startswith("AIN"):
					val = lj.read_ain(ipt)
				elif ipt.startswith("LC"):
					val = lj.read_loadcell_force(ipt)
				elif ipt.startswith("FIO"):
					val = lj.read_dio(ipt)
				else:
					print(f"[WARN] Unknown input type: {ipt}")
				inputs[ipt] = None if val is None else val
			
			# Updates outputs via controller
			outputs = controller.compute(inputs)
			
			# Apply outputs to hardware
			for key, val in outputs.items():
				if key.startswith("FIO"):
					lj.write_dio(key, val)
				elif key.startswith("DAC"):
					lj.write_dac(key, val)
			
			# Pushes data in data_q
			data = {
				"Timestamp": timestamp,
				"TimeABS": time.time(),
				**inputs,
				**outputs
				}
			
			data_q.put(data)
			
			# Pushes reduced_data in plot_q
			reduced_data = {
				"Timestamp": data["Timestamp"],
				**inputs
				}
			plot_q.put(reduced_data)
			
			# Pause (theorically more consistent than time.sleep(interval)
			next_sleep += interval
			sleep_time = max(0, next_sleep - time.time())
			time.sleep(sleep_time)


		except Exception as e:
			print(f"Error in acquisition thread: {e}")
			traceback.print_exc()
			time.sleep(0.1)
