#! /usr/bin/env python

class Metric(object):
	def __init__(self, name):
		self.name = name
	
	def values(self):
		return {'key': (0, 'Count'), 'time': datetime.datetime.now()}
