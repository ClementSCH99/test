# LabJackU6.py

import u6
import time
import logging
import os


class LabJackU6Controller:
	
	def __init__(self, log_dir="logs/", log_file="LabJackU6.log"):
		
		# --- Initialisation logger --- #
		os.makedirs(log_dir, exist_ok=True)
		path = os.path.join(log_dir, log_file)

		self.logger = logging.getLogger(f"LabJackU6-{id(self)}")
		self.logger.setLevel(logging.DEBUG)

		fh = logging.FileHandler(path)
		ch = logging.StreamHandler()
		fh.setLevel(logging.DEBUG)
		ch.setLevel(logging.INFO)

		formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
		fh.setFormatter(formatter)
		ch.setFormatter(formatter)

		if not self.logger.handlers:
			self.logger.addHandler(fh)
			self.logger.addHandler(ch)

		self.logger.info("LabJackU6Controller initialized")

		# --- LabjackU6 connection --- #
		try:
			self.d = u6.U6()
			self.logger.info("LabJackU6 connected")
		except Exception as e:
			self.logger.error(f"LabJackU6 connection not possible: {e}")
			raise
            
		# --- PINS dictionnaries --- #
		self.dio_pins = {f"FIO{i}": i for i in range(8)}
		self.dio_pins.update({f"EIO{i}": i+8 for i in range(8)})
		self.dac_pins = {"DAC0": 0, "DAC1": 1}
		self.adc_pins = {f"AIN{i}": i for i in range(14)}
		
		# --- LoadCell(s) configuration --- #
		self.loadcells = {}


	## -- DIGITAL Functions -- ##
	
	def set_dio_direction(self, pin_name: str, direction_name: str):
		"""Set a DIO as input or output"""
	
		direction_dict = {
			"output": 1,
			"input": 0
			}

		if pin_name not in self.dio_pins:
			self.logger.warning(f"{pin_name} is not a DIO. PIN direction not set")
			return

		if direction_name not in direction_dict:
			self.logger.warning(f"{direction_name} cannot be used as direction. PIN direction not set")
			return
		
		try:
			self.d.getFeedback(u6.BitDirWrite(self.dio_pins[pin_name], direction_dict[direction_name]))
			self.logger.info(f"{pin_name} configured as {direction_name}")
		except Exception as e:
			self.logger.error(f"Failed to set DIO direction on {pin_name}: {e}")


	def write_dio(self, pin_name: str, state: int):
		"""Write a digital state on a DIO"""
		
		if pin_name not in self.dio_pins:
			self.logger.warning(f"{pin_name} is not a valid DIO pin.")
			return
		
		try:
			self.d.getFeedback(u6.BitStateWrite(self.dio_pins[pin_name], state))
			self.logger.debug(f"{pin_name} state changed to {state}")
		except Exception as e:
			self.logger.error(f"Failed to write {pin_name}: {e}")


	def read_dio(self, pin_name: str):
		"""Read a digital state on a DIO"""
		
		if pin_name not in self.dio_pins:
			self.logger.warning(f"{pin_name} is not a valid DIO pin.")
			return None
		
		try:
			r = self.d.getFeedback(u6.BitStateRead(self.dio_pins[pin_name]))
			state = bool(r[0])
			self.logger.debug(f"{pin_name} reads {state}")
			return state
		except Exception as e:
			self.logger.error(f"Failed to read {pin_name}: {e}")
			return None


	## -- ANALOG Functions -- ##
	
	def write_dac(self, pin_name: str, voltage: float):
		"""Write a voltage on DAC0 or DAC1 (0-5V)."""
		
		if pin_name not in self.dac_pins:
			self.logger.warning(f"{pin_name} is not a DAC output.")
			return
		
		if not (0.0 <= voltage <= 5.0):
			self.logger.warning(f"Voltage {voltage}V out of range [0,5].")
			return
		
		voltage_bits = int((voltage/5.0) * 65535)
		
		try:
			if self.dac_pins[pin_name] == 0:
				self.d.getFeedback(u6.DAC0_16(voltage_bits))
			else:
				self.d.getFeedback(u6.DAC1_16(voltage_bits))
			self.logger.debug(f"{pin_name} set to {voltage:.3f}V ({voltage_bits} bits).")
		except Exception as e:
			self.logger.error(f"Failed to write {pin_name}: {e}")

	
	def read_ain(self, pin_name: str):
		"""Read an analog input in volts"""
		
		if pin_name not in self.adc_pins:
			self.logger.warning(f"{pin_name} is not a valid AIN channel.")
			return None
		
		try:
			voltage = self.d.getAIN(self.adc_pins[pin_name])
			self.logger.debug(f"{pin_name} reads {voltage:.5f}V.")
			return voltage
		except Exception as e:
			self.logger.error(f"Failed to read {pin_name}: {e}")
			return None
	
	
	## -- LoadCell functions -- ##
	
	def add_loadcell(self, name, ain_pos: str, ain_neg: str, exc=5.0, rated_F=5.0, mVperV=2e-3, gain_idx=3):
		"""Register a load cell with its parameters"""
		
		if ain_pos not in self.adc_pins:
			self.logger.warning(f"{ain_pos} is not a valid AIN channel.")
			return
		
		if ain_neg not in self.adc_pins:
			self.logger.warning(f"{ain_neg} is not a valid AIN channel.")
			return
		
		if self.adc_pins[ain_neg] != self.adc_pins[ain_pos] + 1:
			self.logger.warning(f"Loadcell {name} uses unsupported AIN pairing ({ain_pos}/{ain_neg}).")
			return
		
		self.loadcells[name] = {
			"AIN_pos": self.adc_pins[ain_pos],
			"AIN_neg": self.adc_pins[ain_neg],
			"Excitation": exc,
			"Rated_Force": rated_F,
			"mV_per_V": mVperV,
			"Offset": 0.0,
			"Gain_idx": gain_idx
			}
		
		self.logger.info(f"Loadcell '{name}' added on {ain_pos}-{ain_neg} with a gain index of {gain_idx}.")
	
	
	def tare_loadcell(self, name, samples=50, delay=0.005):
		"""Perform tare (offset calc.) for a given loadcell"""
		
		if name not in self.loadcells:
			self.logger.warning(f"Loadcell {name} not found for tare.")
			return
		
		acc = 0.0
		count = 0
		
		for s in range(samples):
			val = self.read_loadcell_raw(name)
			if val is not None:
				acc += val
				count += 1
			time.sleep(delay)
		
		if count ==0:
			self.logger.error(f"Tare failed: no valid readings for {name}.")
			return
		
		offset = acc / count
		self.loadcells[name]["Offset"] = offset
		
		self.logger.info(
			f"Loadcell '{name}' tared with offset {offset:.6f} V"
			f"(avg over {count} samples)."
			)
	
	
	def read_loadcell_raw(self, name):
		"""Reads the differential voltage of the loadcell."""
		
		if name not in self.loadcells:
			self.logger.warning(f"Loadcell {name} not found for reading.")
			return
		
		lc = self.loadcells[name]
		
		try:
			voltage = self.d.getAIN(lc["AIN_pos"], gainIndex = lc["Gain_idx"], differential = True)
			self.logger.debug(f"Loadcell '{name}' raw reading: {voltage:.6f}V.")
			return voltage
		except Exception as e:
			self.logger.error(f"Failed to read loadcell '{name}': {e}")
			return None


	def read_loadcell_force(self, name):
		"""Reads loadcell's and returns the force IN ITS OWN UNIT !!!"""
		
		if name not in self.loadcells:
			self.logger.warning(f"Loadcell {name} not found for reading.")
			return
		
		lc = self.loadcells[name]
		
		try:
			raw = self.read_loadcell_raw(name)
			
			if raw is None:
				return None
			
			voltage = raw - lc["Offset"]
			force = (voltage / (lc["Excitation"] * lc["mV_per_V"])) * lc["Rated_Force"]
			self.logger.debug(f"Loadcell '{name}' force: {force:.3f} units.")
			return force
		except Exception as e:
			self.logger.error(f"Failed to read loadcell '{name}' force: {e}")
			return None
	
	
	
	## -- Proper closing -- ##
	
	def close(self, dio_val=0, dac_val=0):
		"""
		Close the LabJack communication, with optional flexible shutdown values
		- dio_vals: int, list or dict
		- dac_vals: int, list or dict
		"""
		
		self.logger.info("Initiation of the closing sequence.")
		
		try:
			
			# Handle DIOs shutdown value
			if isinstance(dio_val, dict):
				for pin_name, pin_val in dio_val.items():
					if pin_name in self.dio_pins:
						self.write_dio(pin_name, pin_val)
						self.logger.info(f"[CLOSING] - {pin_name} set to {pin_val}.")
					else:
						self.logger.warning(f"Ignored invalid DIO pin '{pin_name}' in close().")
			
			elif isinstance(dio_val, list):
				all_dios = list(self.dio_pins.keys())
				for pin_name, pin_val in zip(all_dios, dio_val):
					self.write_dio(pin_name, pin_val)
					self.logger.info(f"[CLOSING] - {pin_name} set to {pin_val}.")
			
			elif isinstance(dio_val, int):
				for pin_name in self.dio_pins:
					self.write_dio(pin_name, dio_val)
				self.logger.info(f"[CLOSING] - All DIOs set to {dio_val}.")
			
			else:
				self.logger.error("Invalid format for dio_val in close(). Expected dict, list or int")
			
			
			# Handle DACs shutdown value
			if isinstance(dac_val, dict):
				for pin_name, pin_val in dac_val.items():
					if pin_name in self.dac_pins:
						self.write_dac(pin_name, pin_val)
						self.logger.info(f"[CLOSING] - {pin_name} set to {pin_val}.")
					else:
						self.logger.warning(f"Ignored invalid DAC pin '{pin_name}' in close().")
			
			elif isinstance(dac_val, list):
				all_dacs = list(self.dac_pins.keys())
				for pin_name, pin_val in zip(all_dacs, dac_val):
					self.write_dac(pin_name, pin_val)
					self.logger.info(f"[CLOSING] - {pin_name} set to {pin_val}.")
			
			elif isinstance(dac_val, int):
				for pin_name in self.dac_pins:
					self.write_dac(pin_name, dac_val)
				self.logger.info(f"[CLOSING] - All DACs set to {dac_val}.")
			
			else:
				self.logger.error("Invalid format for dac_val in close(). Expected dict, list or int")
			
			self.d.close()
			self.logger.info("LabJacku6 closed properly.")
			
		except Exception as e:
			self.logger.error(f"Error while closing LabJacku6 : {e}")
