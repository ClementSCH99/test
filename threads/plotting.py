# threads/plotting.py

import time
import os
import plotly.graph_objects as go
import plotly.io as pio

from collections import deque
from queue import Empty

def loop_plotting(plot_q, running, plot_file, plot_dir="logs/",	 interval: float = 60, maxlen = 5000):
	"""
	Thread to plot data from plot_q.
	Continiously extract data from plot_q until its empty. 
	Then generate a graph, and sleep for interval.
	"""
	
	plot_bf = deque(maxlen = maxlen)
	fig = None
	
	try:
		while running.is_set() or not plot_q.empty():
			
			# Getting all data in the queue
			while True:
				try:
					data = plot_q.get(block = False)
					plot_bf.append(data)
				except Empty:
					break
			
			# Parsing data & making the plot
			if len(plot_bf) > 1:
				timestamps = [d["Timestamp"] for d in plot_bf]
				lc0_vals = [d["LC0"] for d in plot_bf]
			
				fig = go.Figure()
			
				fig.add_trace(go.Scatter(
					x=timestamps,
					y=lc0_vals,
					mode='lines+markers',
					name='LC0'
					))
				
				fig.update_layout(
					xaxis_title='Time [s]',
					yaxis_title='Force [kg]',
					#yaxis_range=[0,5]
					)

				pio.write_html(
					fig,
					file=os.path.join(plot_dir, plot_file),
					auto_open=False
					)
			
			total = 0
			while total < interval and running.is_set():
				time.sleep(1)
				total += 1
	
	except Exception as e:
		print(f"Error in plotting thread: {e}")
		time.sleep(0.01)
	
	finally:
		print("Plot thread closed.")
