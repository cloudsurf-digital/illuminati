#! /usr/bin/env python

import os
import datetime
from sauron import logger
from sauron.metrics import Metric, MetricException

class DiskMetric(Metric):
	def __init__(self, name, path, keys):
		Metric.__init__(self, name, keys)
		self.reconfig(name, path, keys)
	
	def reconfig(self, name, path, keys):
		Metric.reconfig(self, name, keys)
		self.path = path
	
	def values(self):
		# Reference:
		# http://stackoverflow.com/questions/787776/find-free-disk-space-in-python-on-os-x
		try:
			st = os.statvfs(self.path)
			divisor = 1024.0 ** 3
			free  = (st.f_bavail * st.f_frsize) / divisor
			total = (st.f_blocks * st.f_frsize) / divisor
			used  = (st.f_blocks - st.f_bavail) * st.f_frsize / divisor
			results = {
					'free'      : (round(free , 3), 'Gigabytes'),
					'total'     : (round(total, 3), 'Gigabytes'),
					'used'      : (round(used , 3), 'Gigabytes'),
					'percent'   : (round(float(used) / float(total), 3), 'Percent'),
					'inodes'    : (st.f_files, 'Count'),
					'freeInodes': (st.f_ffree, 'Count')
			}
			return {'results': dict((k, results[k]) for k in self.keys)}
		except Exception as e:
			raise MetricException(e)