#! /usr/bin/env python

import os
import urllib2
import datetime
from sauron import logger
from sauron.metrics import Metric, MetricException

class PingMetric(Metric):
	def __init__(self, name, **kwargs):
		Metric.__init__(self, name)
		self.reconfig(name, **kwargs)
		
	def reconfig(self, name, url, post=None, timeout=30):
		self.url  = url
		self.post = post
		self.timeout = timeout	
	
	def values(self):
		start = datetime.datetime.now()
		try:
			result = urllib2.urlopen(self.url, self.post).read()
		except urllib2.HTTPError:
			pass
		except IOError:
			raise MetricException('Failed to fetch %s' % self.url)
		try:
			# Apparently different implementations don't expose this
			latency = (datetime.datetime.now() - start).total_seconds()
		except AttributeError:
			latency = (datetime.datetime.now() - start).seconds
		return {
			'results': {
				'latency': (latency, 'Seconds')
			}
		}