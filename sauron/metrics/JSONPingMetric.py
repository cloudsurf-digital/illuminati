#! /usr/bin/env python

import os
import urllib2
import datetime
import simplejson as json
from sauron import logger
from sauron.metrics import Metric, MetricException

class JSONPingMetric(Metric):
	def __init__(self, name, **kwargs):
		Metric.__init__(self, name)
		self.reconfig(name, **kwargs)
	
	def reconfig(self, name, url, post=None, timeout=30):
		self.name = name
		self.url  = url
		self.post = post
		self.timeout = timeout
	
	def values(self):
		start = datetime.datetime.now()
		results = {}
		try:
			results = json.loads(urllib2.urlopen(self.url, self.post).read())
			results = dict((k,(v, 'Count')) for k,v in results.items())
		except json.decoder.JSONDecodeError as e:
			raise MetricException('Failed to fetch %s : %s' % (self.url, repr(e)))
		except urllib2.HTTPError as e:
			raise MetricException('Failed to fetch %s : %s' % (self.url, repr(e)))
		except IOError as e:
			raise MetricException('Failed to fetch %s : %s' % (self.url, repr(e)))
		# Some systems are stupid, and don't have total_seconds
		try:
			results['latency'] = ((datetime.datetime.now() - start).total_seconds(), 'Seconds')
		except AttributeError:
			results['latency'] = ((datetime.datetime.now() - start).seconds, 'Seconds')
		return {
			'results': results
		}