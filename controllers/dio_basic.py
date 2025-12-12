# controllers/dio_basic.py

from .base import BaseController
from typing import Dict, Any

class DioBasicController(BaseController):
	
	def __init__(self, hysterisis: float = 0.05, thresholds: Dict=None):
		
		#Init from super Class
		super().__init__()
		
		self.hysterisis = hysterisis
		self.thresholds = thresholds or {
			"FIO0": 2.0,
			"FIO1": 3.0,
			"FIO2": 3.5,
			"FIO3": 4.0,
			}
			
		# persistent state for each output
		self.states = {key: 0 for key in self.thresholds}
		
		# Required inputs
		self.required_inputs = ["AIN0"]


	def compute(self, inputs: Dict[str, float]) -> Dict[str, float]:
		"""Provides outpus desired states based on AIN0 value, with hysterisis for falling Hedge"""
		
		ain0 = inputs.get("AIN0")
		outputs = {}
		
		# If no new measurement, keep last states
		if ain0 is None:
			return self.states.copy()
		
		for pin, thr in self.thresholds.items():
			prev = self.states[pin]
			
			# Rising Hedge
			if ain0 >= thr and not prev:
				self.states[pin] = 1
			
			# Falling Hede
			elif ain0 < thr - self.hysterisis and prev:
				self.states[pin] = 0
			
			outputs[pin] = self.states[pin]
		
		return outputs
