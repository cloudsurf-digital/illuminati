#! /usr/bin/env python

import os
import Metric
import MySQLdb
import datetime

class MySQLMetric(Metric.Metric):
	def __init__(self, name, host=None, user=None, passwd=None):
		super(MySQLMetric,self).__init__(name)
		self.host   = host
		self.user   = user
		self.passwd = passwd
	
	def values(self):
		try:
			conn = MySQLdb.connect(host=self.host, user=self.user, passwd=self.passwd)
			cursor = conn.cursor()
			cursor.execute('show status')
			r = dict(cursor.fetchall())
			return {
				'results' : {
					'uptime' : (r['Uptime'] , 'Seconds'),
					'queries': (r['Queries'], 'Count')
				}
			}
		except MySQLdb.OperationalError:
			raise Metric.MetricException('Failed to connect to mySQL.')
		except KeyError:
			raise Metric.MetricException('Could not find all keys in mySQL status')
	