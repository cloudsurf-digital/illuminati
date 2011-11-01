#! /usr/bin/env python

import psutil
import datetime
from sauron import logger
from sauron.metrics import Metric, MetricException

class SystemMetric(Metric):
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
			raise MetricException(e)
		except psutil.error.AccessDenied as e:
			raise MetricException('Access denied in psutil')
