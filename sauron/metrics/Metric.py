#! /usr/bin/env python

class MetricException(Exception):
	def __init__(self, message):
		self.msg = message
	def __repr__(self):
		return repr(self.msg)
	def __str__(self):
		return str(self.msg)

class Metric(object):
	def __init__(self, name, keys=None):
		self.name = name
		self.keys = keys
	
	def getValues(self):
		if self.keys:
			results = self.values()
			results['results'] = dict((k, results['results'][k]) for k in self.keys)
			return results
		else:
			return self.values()
	
	def values(self):
		return {
			'results': {
				'key': (0, 'Count')
			}, 'time': datetime.datetime.now()
		}
