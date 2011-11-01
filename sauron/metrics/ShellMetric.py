#! /usr/bin/env python

import re
import subprocess
from sauron import logger
from sauron.metrics import Metric, MetricException

class ShellMetric(Metric):
	def __init__(self, name, cmd, units):
		Metric.__init__(self, name)
		self.reconfig(name, cmd, units)
	
	def reconfig(self, name, cmd, units):
		self.cmd   = cmd
		self.units = units
	
	def values(self):
		try:
			res = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
			return {'results' : { self.name : (res, self.units) } }
		except ValueError:
			raise MetricException('Invalid call to Popen for %s' % cmd)
		except OSError as e:
			raise MetricException(e)

if __name__ == '__main__':
	m = ShellMetric('testing', **{'count':'ls -l | wc -l', 'count-units':'Count'})
	print repr(m.values())