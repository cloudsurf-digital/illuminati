#! /usr/bin/env python

import os
import MySQLdb
import datetime
from metric import Metric

class MySQLMetric(Metric):
	def __init__(self, name, host=None, user=None, passwd=None):
		super(MySQLMetric,self).__init__(name)
		self.host   = host
		self.user   = user
		self.passwd = passwd
	
	def values(self):
		conn = MySQLdb.connect(host=self.host, user=self.user, passwd=self.passwd)
		cursor = conn.cursor()
		try:
			cursor.execute('show status')
			r = dict(cursor.fetchall())
			return {
				'results' : {
					'uptime' : (r['Uptime'] , 'Seconds'),
					'queries': (r['Queries'], 'Count')
				}
			}
		except MySQLdb.OperationalError:
			return {'error': 'Failed to connect to mySQL'}
		except KeyError:
			return {'error': 'Could not find all keys in mySQL status'}
	