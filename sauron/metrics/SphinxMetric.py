#! /usr/bin/env python

import os
import Metric
import pymysql
import datetime

class SphinxMetric(Metric.Metric):
	def __init__(self, name, host='127.0.0.1', port=9306):
		super(SphinxMetric,self).__init__(name)
		self.host   = host
		self.port   = port
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
			self.conn = pymysql.connect(host=self.host, port=self.port)
			self.cur = self.conn.cursor()
			self.cur.execute('show status')
			r = dict(self.cur.fetchall())
			return {
				'results' : {
					'uptime'   : (r['uptime'], 'Seconds'),
					'queries'  : (r['queries'], 'Count'),
					'avg_wall' : (r['avg_query_wall'], 'Seconds'),
					'avg_cpu'  : (r['avg_query_cpu'], 'Percent'),
					'avg_read' : (r['avg_query_readkb'], 'Kilobytes')
				}
			}
		except pymysql.err.MySQLError:
			raise Metric.MetricException('Error connecting to sphinx searchd')
		except KeyError:
			raise Metric.MetricException('Could not find all keys in searchd status')
