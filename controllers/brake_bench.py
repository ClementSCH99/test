# controllers/brake_bench.py

from .base import BaseController
from typing import Dict, Any
from collections import deque
import time

class BrakeBenchController(BaseController):
	
	def __init__(self, target_up=-111.0, target_down=-1.0, max_cycles=10000, rest_time=1.0):
		
		# Variable storage
		self.phase = "idle"
		self.cycle_counter = 0
		self.target_up = target_up
		self.target_down = target_down
		self.max_cycles = max_cycles
		self.rest_time = rest_time
		self.phase_start = None
		self.last_force = None
		
		# Variable for ETA and CPM
		self.cycle_timestamps = deque(maxlen=200)
		self.cycle_speed = 0.0
		self.eta_s = None
		
		# Variable for Push timing tracking
		self.push_start = None
		self.push_times = deque(maxlen=200)
		self.last_push_duration = None
		self.avg_push_duration = None
		
		# Initialise outputs states at 1 (rest - inverted because of relay board)
		self.states = {
			"FIO0": 1,
			"FIO1": 1
			}
		
		# Required inputs
		self.required_inputs = ["LC0"]
		
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
	
	def _on_push_completed(self):
		"""Compute timing stats when a pushing phase completes."""
		
		if self.push_start is None:
			return
		
		duration = time.time() - self.push_start
		self.last_push_duration = duration
		
		self.push_times.append(duration)
		
		if len(self.push_times) > 0:
			self.avg_push_duration = sum(self.push_times) / len(self.push_times)
		else:
			self.avg_push_duration = None
	
	
	### -- STATE MACHINES -- ###	
	def _state_idle(self, force):
		self.states["FIO0"] = 0
		self.states["FIO1"] = 1
		self.cycle_counter += 1
		return self.transition("pushing")
	
	def _state_pushing(self, force):
		if self.push_start is None:
			self.push_start = time.time()
		
		if force < self.target_up:
			self.last_force = force
			
			self.states["FIO0"] = 1
			self.states["FIO1"] = 1
			
			self._on_push_completed()
			self.push_start = None
			
			return self.transition("wait_after_push")
		return None
	
	def _state_wait_after_push(self, force):
		if time.time() - self.phase_start > self.rest_time:
			self.states["FIO0"] = 1
			self.states["FIO1"] = 0
			return self.transition("pulling")
		return None
	
	def _state_pulling(self, force):
		if force > self.target_down:
			self.states["FIO0"] = 1
			self.states["FIO1"] = 1
			return self.transition("wait_after_pull")
		return None
	
	def _state_wait_after_pull(self, force):
		if time.time() - self.phase_start > self.rest_time:
			self.cycle_counter += 1
			self._on_cycle_completed()
			
			if self.cycle_counter >= self.max_cycles:
				return self.transition("end_of_test")
			else:
				self.states["FIO0"] = 0
				self.states["FIO1"] = 1
			return self.transition("pushing")
			
		return None
	
	def _state_end(self, force):
		self.states["FIO0"] = 1
		self.states["FIO1"] = 0
		return None
	
	
	def compute(self, inputs: Dict[str, float]) -> Dict[str, Any]:
		"""
		Provides controls outputs for brake cycling test, based on current reading.
		- Inputs shall contain "LC0" (with its force expressed in N)
		- Outputs a dictionnaire such as {"FIO1": 0, "FIO2": 1, "phase": ...}
		"""
		
		force = inputs.get("LC0")
		if force is None:
			return self.states.copy()
		
		handler = self.handler[self.phase]
		new_phase = handler(force)
		
		outputs = {
			**self.states,
			"phase": self.phase,
			"cycle_count": self.cycle_counter,
			"cycle_cpm": self.cycle_speed,
			"eta_s": self.eta_s,
			"push_avg" : self.avg_push_duration
			}
		
		return outputs
	
	
	
	
	
	
	
	
	### -- OLD FUNCTION TO BE IGNORED -- ###
	
	def compute_old(self, inputs: Dict[str, float]) -> Dict[str, Any]:
		"""
		Provides controls outputs for brake cycling test, based on current reading.
		- Inputs shall contain "LC0" (with its force expressed in N)
		- Outputs a dictionnaire such as {"FIO1": 0, "FIO2": 1, "status": ...}
		"""
		
		force = inputs.get("LC0")
		now = time.time()
		outputs = {}
		
		# If no new measurement, keep last states
		if force is None:
			return self.states.copy()
		
		
		# Controls logic
		if self.phase == "idle":
			
			# Start puhsing
			self.states["FIO0"] = 0
			self.states["FIO1"] = 1
			self.phase = "pushing"
			self.cycle_counter += 1
		
		elif self.phase == "pushing":
			if force > self.target_up:
				
				# Stop pushing and start waiting
				self.states["FIO0"] = 1
				self.states["FIO1"] = 1
				self.phase_start = now
				self.phase = "wait_after_push"
		
		elif self.phase == "wait_after_push":
			if now - self.phase_start > self.rest_time:
				
				# Stop waiting and start pulling
				self.states["FIO0"] = 1
				self.states["FIO1"] = 0
				self.phase = "pulling"
		
		elif self.phase == "pulling":
			if force < self.target_down:
				
				# Stop pulling and start waiting
				self.states["FIO0"] = 1
				self.states["FIO1"] = 1
				self.phase_start = now
				self.phase = "wait_after_pull"
		
		elif self.phase == "wait_after_pull":
			if now - self.phase_start > self.rest_time:
				if self.cycle_counter >= self.max_cycles:
					
					# Stop cycling
					self.phase = "end_of_test"
				else:
					
					# Start pushing
					self.states["FIO0"] = 0
					self.states["FIO1"] = 1
					self.phase = "pushing"
					self.cycle_counter += 1
		
		# Write states and phase in outputs
		outputs = self.states.copy()
		outputs["phase"] = self.phase
		
		return outputs
