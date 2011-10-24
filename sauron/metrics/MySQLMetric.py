#! /usr/bin/env python

import os
import Metric
import pymysql
import datetime

class MySQLMetric(Metric.Metric):
	def __init__(self, name, host=None, user=None, passwd=None):
		Metric.Metric.__init__(self, name)
		self.reconfig(name, host, user, passwd)
	
	def reconfig(self, name, host=None, user=None, passwd=None):
		self.name   = name
		self.host   = host
		self.user   = user
		self.passwd = passwd
		self.conn   = None
		self.cur    = None
	
	def __del__(self):
		try:
			self.cur.close()
			self.conn.close()
		except AttributeError:
			pass
	
	def values(self):
		try:
			self.conn = pymysql.connect(host=self.host, user=self.user, passwd=self.passwd)
			self.cur = self.conn.cursor()
			self.cur.execute('show status')
			r = dict(self.cur.fetchall())
			return {
				'results' : {
					'uptime' : (r['Uptime'] , 'Seconds'),
					'queries': (r['Queries'], 'Count')
				}
			}
		except pymysql.err.MySQLError:
			raise Metric.MetricException('Failed to connect to mySQL.')
		except KeyError:
			raise Metric.MetricException('Could not find all keys in mySQL status')
	