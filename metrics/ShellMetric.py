#! /usr/bin/env python

import re
import subprocess
from metric import Metric

class ShellMetric(Metric):
	def __init__(self, name, **kwargs):
		super(ShellMetric,self).__init__(name)
		self.metrics = {}
		self.units = {}
		# Go head and set up all the metrics
		for met, cmd in kwargs.items():
			if re.search(r'-units$', met):
				unit = met.replace('-units', '')
				print 'Found units for %s' % unit
				self.units[unit] = cmd
			else:
				self.metrics[met] = cmd
		# Now make sure each metric has a unit
		for met in self.metrics:
			if met not in self.units:
				print 'No units provided for %s!' % met
				exit(1)
	
	def values(self):
		results = {}
		for met, cmd in self.metrics.items():
			try:
				res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
				results[met] = (res, self.units[met])
			except ValueError:
				return { 'error' : 'Invalid call to Popen for %s' % cmd}
			except OSError as e:
				return { 'error' : repr(e) }
		return { 'results' : results }

if __name__ == '__main__':
	m = ShellMetric('testing', **{'count':'ls -l | wc -l', 'count-units':'Count'})
	print repr(m.values())