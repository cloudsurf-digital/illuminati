#! /usr/bin/env python

import os
import MySQLdb
import datetime
from metric import Metric

class SphinxMetric(Metric):
	def __init__(self, name, host='127.0.0.1', port=9306):
		super(SphinxMetric,self).__init__(name)
		self.host   = host
		self.port   = port
	
	def values(self):
		try:
			conn = MySQLdb.connect(host=self.host, port=self.port)
			cursor = conn.cursor()
			cursor.execute('show status')
			r = dict(cursor.fetchall())
			return {
				'results' : {
					'uptime'   : (r['uptime'], 'Seconds'),
					'queries'  : (r['queries'], 'Count'),
					'avg_wall' : (r['avg_query_wall'], 'Seconds'),
					'avg_cpu'  : (r['avg_query_cpu'], 'Percent'),
					'avg_read' : (r['avg_query_readkb'], 'Kilobytes')
				}
			}
		except MySQLdb.OperationalError:
			return {'error': 'Error connecting to sphinx searchd'}
		except KeyError:
			return {'error': 'Could not find all keys in searchd status'}
