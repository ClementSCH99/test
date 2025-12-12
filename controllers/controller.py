# controller.py

class DioController:
	"""
	State-mahcine controlling DIO outputs based on AIN measurement.
	Class need to be reworked based on project need.
	"""
	
	def __init__(self, hysteresis: float = 0.05):
		
		self.hysteresis = hysteresis
		
		# Persistent state-machine
		self.conditions = [
		{"dio": "FIO0", "state": False, "value": 0},
		{"dio": "FIO1", "state": False, "value": 0},
		{"dio": "FIO2", "state": False, "value": 0},
		{"dio": "FIO3", "state": False, "value": 0}
		]


	def update_dio_T00(self, device, ain_vals: list):
		"""
		Update Digital Output state based on the AIN0 value.
		Returns a list of DIO states [0/1, 0/1, 0/1, 0/1].
		This logic was made for debug purpose.
		"""
		
		dio_states = []
		
		# Selection of the used Analog input
		ain0_val = ain_vals[0]
		
		# Conditions threshold definition
		self.conditions[0]["threshold"] = 2.0
		self.conditions[1]["threshold"] = 3.0
		self.conditions[2]["threshold"] = 3.5
		self.conditions[3]["threshold"] = 4.0
		
		for i, cond in enumerate(self.conditions):
			
			previous_val = cond["value"]
			
			# Rising edge
			if ain0_val > cond["threshold"] and not cond["state"]:
				cond["value"] = 1
				cond["state"] = True
				device.logger.debug(
				f"{cond['dio']} -> HIGH (AIN={ain0_val:.3f}V > {cond['threshold']}V)"
				)
		
			# Falling edge
			if ain0_val < cond["threshold"] - self.hysteresis and cond["state"]:
				cond["value"] = 0
				cond["state"] = False
				device.logger.debug(
				f"{cond['dio']} -> LOW (AIN={ain0_val:.3f}V < {cond['threshold']}V)"
				)
		
			# Apply to device
			if cond["value"] != previous_val:
				device.write_dio(cond["dio"], cond["value"])
			
			# Store state to DIOs list
			dio_states.append(cond["value"])
		
		return dio_states


class DacController:
	"""
	Signal generator for DAC outputs.
	Class needs to be reworked based on project need.
	"""
	
	def __init__(self, amplitude: float = 5, offset: float = 0, frequency: float = 0.1, waveform: str = "sine"):
		self.amplitude = amplitude
		self.offset = offset
		self.frequency = frequency
		self.waveform = waveform

	def update_dac(self, device, t):
		
		dac_vals = []
		
		for dac_name in device.dac_pins:
				
			if self.waveform == "sine":
				import math
				volt = max(0, min(5, self.amplitude * math.sin(2*math.pi*self.frequency*t) + self.offset))
				
			elif self.waveform == "step":
				volt = 5 if (t % 2) < 1 else 0
				
			else:
				volt = self.offset
			
			device.write_dac(dac_name, volt)
			dac_vals.append(volt)
		
		return dac_vals

