#! /usr/bin/env python

import Emitter
import urllib2			# Need this to determine our instance ID
import datetime
from boto.ec2.cloudwatch import CloudWatchConnection

class CloudWatch(Emitter.Emitter):
	def __init__(self, namespace):
		super(CloudWatch,self).__init__()
		self.namespace = namespace
		self.conn = CloudWatchConnection()
		self.meta = {}
		# Try to find the instance ID
		try:
			self.meta['InstanceId'] = urllib2.urlopen('http://169.254.169.254/1.0/meta-data/instance-id', timeout=1.0).read().strip()
		except urllib2.URLError:
			self.logger.warn('Failed to get an instance ID for this node from Amazon')
	
	def metrics(self, metrics):
		t = datetime.datetime.now()
		for name, results in metrics.items():
			for key,value in results.items():
				self.logger.info('Pushing %s-%s => %s' % (name, key, repr(value)))
				v, u = value
				self.conn.put_metric_data(self.namespace, name + '-' + key, timestamp=t, unit=u, value=v, dimensions=self.meta)
	
