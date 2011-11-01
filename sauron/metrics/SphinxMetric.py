#! /usr/bin/env python

import os
import pymysql
import datetime
from sauron import logger
from sauron.metrics import Metric, MetricException

class SphinxMetric(Metric):
	def __init__(self, name, host='127.0.0.1', port=9306):
		Metric.__init__(self, name)
		self.reconfig(name, host, port)
	
	def reconfig(self, name, host='127.0.0.1', port=9306):
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
			raise MetricException('Error connecting to sphinx searchd')
		except KeyError:
			raise MetricException('Could not find all keys in searchd status')
