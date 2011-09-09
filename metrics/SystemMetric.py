#! /usr/bin/env python

import psutil
import Metric
import datetime

class SystemMetric(Metric.Metric):
	def __init__(self, name):
		super(SystemMetric,self).__init__(name)
	
	def values(self):
		try:
			phys = psutil.phymem_usage()
			virt = psutil.virtmem_usage()
			return {'results': {
					'physical': (phys.percent, 'Percent'),
					'virtual' : (virt.percent, 'Percent')
				}
			}
		except OSError as e:
			raise Metric.MetricException(e)
		except psutil.error.AccessDenied as e:
			raise Metric.MetricException('Access denied in psutil')
