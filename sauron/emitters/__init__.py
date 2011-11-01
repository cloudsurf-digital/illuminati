#! /usr/bin/env python

from sauron import logger

class EmitterException(Exception):
	def __init__(self, message):
		self.msg = message
	def __repr__(self):
		return repr(self.msg)
	def __str__(self):
		return str(self.msg)

class Emitter(object):
	def metrics(self, metrics):
		for k,m in metrics.items():
			for metric,value in m['results'].items():
				logger.info('\t%s-%s => %s' % (k,metric,repr(value)))