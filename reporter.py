#! /usr/bin/env python

import time				# For sleeping
import urllib			# Need this to determine our instance ID
import logging			# Log nicely
import datetime			# For default times
import ConfigParser		# For reading default configurations
from boto.ec2.cloudwatch import CloudWatchConnection

logger = logging.getLogger('sauron')
logger.addHandler(logging.NullHandler())

class Watcher(object):
	@staticmethod
	def getInstanceId():
		return urllib.urlopen('http://169.254.169.254/1.0/meta-data/instance-id').read().strip()
	
	def __init__(self):
		self.conn      = CloudWatchConnection()
		self.metrics   = []
		self.readConfig()
	
	def readConfig(self):
		self.config    = ConfigParser.ConfigParser()
		# Try to read from each of these in order
		self.config.read(['sauron.conf', '/etc/sauron.conf'])
		try:
			d = dict(self.config.items('sauron'))
		except ConfigParser.NoSectionError:
			print 'No sauron section in configuration file.'
			logging.error('No sauron section in configuration file.')
			exit(1)
		for section in self.config.sections():
			if section == 'sauron':
				defaults = {'interval': 500}
				defaults.update(dict(self.config.items(section)))
				if 'namespace' not in defaults:
					defaults['namespace'] = self.getInstanceId()
				try:
					self.interval  = int(defaults['interval'])
					self.namespace = defaults['namespace']
				except KeyError as e:
					print '%s' % repr(e)
					logging.error(repr(e))
					exit(2)
			else:
				m = __import__('metrics.%s' % section)
				c = getattr(m, section)
				c = getattr(c, section)
				d = dict(self.config.items(section))
				try:
					d['keys'] = [key.strip() for key in d['keys'].split(',')]
				except KeyError:
					pass
				obj = c(**d)
				self.metrics.append(obj)
	
	def push(self, metric):
		self.metrics.append(metric)
	
	def run(self):
		while True:
			next = time.time() + self.interval
			logging.info('Reporting metrics...')
			for m in self.metrics:
				results = m.values()
				logging.info('Querying %s' % m.name)
				try:
					# The default time is now
					try:
						t = results['time']
					except KeyError:
						t = datetime.datetime.now()
						logging.debug('No time provided by metric. Using now.')
					# Go through all the results
					for key in results['results']:
						logging.info('Pushing %s' % key)
						v, u = results['results'][key]
						self.conn.put_metric_data(self.namespace, m.name + '-' + key, timestamp=t, unit=u, value=v)
				except KeyError as e:
					logging.error('Key Error : %s' % repr(e))
			# Sleep until we should next run it
			time.sleep(next - time.time())

if __name__ == '__main__':
	w = Watcher()
	w.run()