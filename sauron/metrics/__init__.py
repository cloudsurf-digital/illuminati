#! /usr/bin/env python

import os
import sys
from sauron import logger

# Append our current path before this import
p = os.path.dirname(os.path.abspath(__file__))
if p not in sys.path:
	sys.path.insert(0, p)

class MetricException(Exception):
	def __init__(self, message):
		self.msg = message
	def __repr__(self):
		return repr(self.msg)
	def __str__(self):
		return str(self.msg)

class Metric(object):
	def __init__(self, name, keys=[]):
		Metric.reconfig(self, name, keys)
	
	def reconfig(self, name, keys=[]):
		self.name = name
		self.keys = keys
	
	def getValues(self):
		if self.keys:
			results = self.values()
			pruned = {}
			for k in self.keys:
				try:
					pruned[k] = results['results'][k]
				except KeyError:
					logger.warn('Key %s unavailable' % k)
			results['results'] = pruned
			return results
		else:
			return self.values()
	
	def values(self):
		return {
			'results': {
				'key': (0, 'Count')
			}, 'time': datetime.datetime.now()
		}
