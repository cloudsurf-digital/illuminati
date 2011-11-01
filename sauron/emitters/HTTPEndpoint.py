#! /usr/bin/env python

import httplib2
import simplejson as json
from sauron import logger
from sauron.emitters import Emitter, EmitterException

class HTTPEndpoint(Emitter):
	def __init__(self, url, method='PUT'):
		super(HTTPEndpoint,self).__init__()
		self.url = url
		self.method = method
	
	def metrics(self, metrics):
		d = {}
		for name, results in metrics.items():
			for key,value in results['results'].items():
				d[name + '-' + key] = value
		try:
			response, content = httplib2.Request(self.url, method=self.method, body=json.dumps(d))
			if response != 200:
				logger.error('%s responded with (%i) %s' % (self.url, response, content))
		except httplib2.HttpLib2Error as e:
			logger.error(repr(e))

	
