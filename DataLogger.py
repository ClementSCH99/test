# DataLogger.py

import csv
import time
import os

class DataLogger:
	
	def __init__(self, save_file, save_dir="logs/", autosave_interval=None, autosave_file=None):
		
		self.data = []
		self.save_file = save_file
		self.save_dir = save_dir
		self.autosave_interval = autosave_interval
		self.autosave_file = autosave_file
		
		self.last_save = time.time() if autosave_interval else None
	
	
	def log(self, data: dict):
		""" 
		Log data in a temp list.
		Data content is based on controller required inputs and outputs.
		log is responsible of autosave mechanism
		"""
		
		# Data parsing and storing
		entry = data
		self.data.append(entry)
		
		# Autosave mechanisme
		if self.autosave_interval and self.autosave_file:
			now = time.time()
			if now - self.last_save >= self.autosave_interval:
				self._autosave(os.path.join(self.save_dir, self.autosave_file))
				self.last_save = now
	
	
	def _autosave(self, filename):
		"""Internal autosave function"""
		
		if not self.data:
			return
		
		keys = self.data[0].keys()

		with open(filename, "w", newline="") as f:
			writer = csv.DictWriter(f, fieldnames=keys)
			writer.writeheader()
			writer.writerows(self.data)
        
		print(f"[AUTOSAVE] Periodic save done -> {self.autosave_file}")


	def save_csv(self):
		"""Explicit save (manual or final)"""
		
		if not self.data:
			print("No data to save")
			return
			
		keys = self.data[0].keys()

		with open(os.path.join(self.save_dir, self.save_file), "w", newline="") as f:
			writer = csv.DictWriter(f, fieldnames=keys)
			writer.writeheader()
			writer.writerows(self.data)
        
		print(f"[SAVE] Data saved -> {self.save_file}")
		
		if self.autosave_file and os.path.exists(os.path.join(self.save_dir, self.autosave_file)):
			try:
				os.remove(os.path.join(self.save_dir, self.autosave_file))
				print(f"[CLEANUP] Autosave file removed -> {self.autosave_file}")
			except Exception as e:
				print(f"Coudl not remove autosave file: {e}")
