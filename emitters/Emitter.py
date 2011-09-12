#! /usr/bin/env python

import logging

class EmitterException(Exception):
	def __init__(self, message):
		self.message = message
	def __repr__(self):
		return repr(self.message)
	def __str__(self):
		return str(self.message)

class Emitter(object):
	def __init__(self):
		self.logger = logging.getLogger('sauron')
	
	def metrics(self, metrics):
		pass