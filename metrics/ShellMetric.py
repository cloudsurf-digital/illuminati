#! /usr/bin/env python

import re
import Metric
import subprocess

class ShellMetric(Metric.Metric):
	def __init__(self, name, cmd, units):
		super(ShellMetric,self).__init__(name)
		self.cmd   = cmd
		self.units = units
	
	def values(self):
		try:
			res = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
			return {'results' : { self.name : (res, self.units) } }
		except ValueError:
			raise Metric.MetricException('Invalid call to Popen for %s' % cmd)
		except OSError as e:
			raise Metric.MetricException(e)

if __name__ == '__main__':
	m = ShellMetric('testing', **{'count':'ls -l | wc -l', 'count-units':'Count'})
	print repr(m.values())