# controllers/base.py

from typing import Dict, Any
import time

class BaseController:
	"""
	Base cxontroller class providing a standard interface for all bench controllers.
	
	Each contronller must define:
	- self.required_inputs: list[str]
	- self.states: persistent outputs ({pin: value})
	- self.phase: current state-machine phase
	- self.handler: dict mapping phase name -> handler function(inputs)
	"""
	
	def __init__(self):
		self.required_inputs = []
		self.states = {}
		self.phase = "idle"
		self.phase_start = None
		self.handler = {}
	
	def transition(self, new_phase: str):
		"""Switch to a new phase and reset its start timestamp."""
		self.phase = new_phase
		self.phase_start = time.time()
		return new_phase
	
	
	def compute(self, inputs: Dict[str, float]) -> Dict[str, Any]:
		"""
		Main logic dispatcher.
		- Calls the handler associated with the current phase.
		- Update outputs accordingly.
		"""
		
		raise NotImplementedError
