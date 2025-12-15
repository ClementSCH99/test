# controllers/trim_bench.py

from .base import BaseController
from typing import Dict, Any
from collections import deque
import time

class TrimBenchController(BaseController):
	
	def __init__(self, max_cycles=10000, rest_time=1.0):
		
		# Variable storage
		self.phase = "idle"
		self.cycle_counter = 0
		self.max_cycles = max_cycles
		self.rest_time = rest_time
		self.phase_start = None
		
		# Variable for ETA and CPM
		self.cycle_timestamps = deque(maxlen=200)
		self.cycle_speed = 0.0
		self.eta_s = None
		
		# Required inputs
		self.required_inputs = ["FIO2", "FIO3"]
		
		# Initialise outputs states at 1 (rest - inverted because of relay board)
		self.states = {
			"FIO0": 1,
			"FIO1": 1
			}
		
		# State handler for more clarity
		self.handler = {
			"idle": self._state_idle,
			"pushing": self._state_pushing,
			"wait_after_push": self._state_wait_after_push,
			"pulling": self._state_pulling,
			"wait_after_pull": self._state_wait_after_pull,
			"end_of_test": self._state_end
			}
	
	
	### -- Fonction for statistics -- ###
	def _on_cycle_completed(self):
		"""Fucntion called when a cycle finishes."""
		
		now = time.time()
		self.cycle_timestamps.append(now)
		
		# CPM calculcation
		if len(self.cycle_timestamps) > 2:
			dt = self.cycle_timestamps[-1] - self.cycle_timestamps[0]
			n = len(self.cycle_timestamps) -1
			self.cycle_speed = (n / dt) * 60
		else:
			self.cycle_speed = 0.0
		
		# ETA calculation
		remaining = self.max_cycles - self.cycle_counter
		if self.cycle_speed > 0:
			self.eta_s = remaining / self.cycle_speed * 60
		else:
			self.eta_seconds = None
	
	
	### -- STATE MACHINES -- ###	
	def _state_idle(self, switches):
		self.states["FIO0"] = 1
		self.states["FIO1"] = 0
		self.cycle_counter += 1
		return self.transition("pushing")
	
	def _state_pushing(self, switches):
		if switches["push_end"]:
			self.states["FIO0"] = 0
			self.states["FIO1"] = 0
			return self.transition("wait_after_push")
		return None
	
	def _state_wait_after_push(self, switches):
		if time.time() - self.phase_start > self.rest_time:
			self.states["FIO0"] = 0
			self.states["FIO1"] = 1
			return self.transition("pulling")
		return None
	
	def _state_pulling(self, switches):
		if switches["pull_end"]:
			self.states["FIO0"] = 0
			self.states["FIO1"] = 0
			return self.transition("wait_after_pull")
		return None
	
	def _state_wait_after_pull(self, switches):
		if time.time() - self.phase_start > self.rest_time:
			self.cycle_counter += 1
			self._on_cycle_completed()
			
			if self.cycle_counter >= self.max_cycles:
				return self.transition("end_of_test")
			else:
				self.states["FIO0"] = 1
				self.states["FIO1"] = 0
			return self.transition("pushing")
			
		return None
	
	def _state_end(self, switches):
		self.states["FIO0"] = 0
		self.states["FIO1"] = 1
		return None
	
	
	### -- Compute Function -- ###
	def compute(self, inputs: Dict[str, float]) -> Dict[str, Any]:
		"""
		Provides controls outputs for brake cycling test, based on current reading.
		- Inputs shall contain "FIO2" & "FIO3" (DIOs set as input, for end of travel indication)
		- Outputs a dictionnaire such as {"FIO1": 0, "FIO2": 1, "phase": ...}
		"""
		
		for key in self.required_inputs:
			if inputs.get(key) is None:
				return self.states.copy()
		
		switches = {
			"push_end": inputs.get("FIO2"),
			"pull_end": inputs.get("FIO3")
			}
		
		handler = self.handler[self.phase]
		handler(switches)
		
		outputs = {
			**self.states,
			"phase": self.phase,
			"cycle_count": self.cycle_counter,
			"cycle_cpm": self.cycle_speed,
			"eta_s": self.eta_s,
			}
		
		return outputs
