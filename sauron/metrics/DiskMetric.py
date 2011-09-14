#! /usr/bin/env python

import os
import Metric
import datetime

class DiskMetric(Metric.Metric):
	def __init__(self, name, path, keys):
		super(DiskMetric,self).__init__(name)
		self.path = path
		self.keys = keys
	
	def values(self):
		# Reference:
		# http://stackoverflow.com/questions/787776/find-free-disk-space-in-python-on-os-x
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
