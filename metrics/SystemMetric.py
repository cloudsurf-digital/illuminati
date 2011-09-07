#! /usr/bin/env python

import psutil
import datetime
from metric import Metric

class SystemMetric(Metric):
	def __init__(self, name):
		super(SystemMetric,self).__init__(name)
	
	def values(self):
		try:
			phys = psutil.phymem_usage()
			virt = psutil.virtmem_usage()
			return {'results': {
					'physical': phys.percent,
					'virtual' : virt.percent
				}
			}
		except OSError as e:
			return {'error': repr(e)}
		except psutil.error.AccessDenied as e:
			return {'error': repr(e)}
