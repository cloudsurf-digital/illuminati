#! /usr/bin/env python

import os
import urllib2
import datetime
from metric import Metric

class PingMetric(Metric):
	def __init__(self, name, url, post=None, timeout=30):
		super(PingMetric,self).__init__(name)
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
			return {'error': 'Failed to fetch %s' % self.url}
		latency = (datetime.datetime.now() - start).total_seconds()
		return {
			'results': {
				'latency': (latency, 'Seconds')
			}
		}