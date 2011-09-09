#! /usr/bin/env python

class MetricException(Exception):
	def __init__(self, message):
		self.message = message
	def __repr__(self):
		return repr(self.message)
	def __str__(self):
		return str(self.message)

class Metric(object):
	def __init__(self, name):
		self.name = name
	
	def values(self):
		return {'key': (0, 'Count'), 'time': datetime.datetime.now()}
