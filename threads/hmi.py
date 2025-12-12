# threads/hmi.py

import time
import os

def loop_hmi(controller, running, refresh=1.0):
	"""Threads for HMI"""
	
	while running.is_set() and controller.phase != "end_of_test":
		os.system("cls" if os.name == "nt" else "clear")
		print("=== Bake Bench MONITOR ===")
		print(f"Cycle		: {controller.cycle_counter}")
		print(f"Phase		: {controller.phase}")
		print(f"Force (LC0)	: {controller.last_force:.2f}N" if controller.last_force else "Force (LC0)	: --")
		print(f"Cycle speed	: {controller.cycle_speed:.2f} cpm" if controller.cycle_speed else "Cycle speed	: --")
		print(f"Push AVG	: {controller.avg_push_duration:.2f}s" if controller.avg_push_duration else "Push AVG	: --")
		print("------------------------------------------")
		print(f"ETA		: {controller.eta_s/60:.1f}min" if controller.eta_s else "ETA		: --")
		
		time.sleep(refresh)
