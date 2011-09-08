#! /usr/bin/env python

import re
import os
import psutil
import datetime
from metric import Metric

class ProcMetric(Metric):
	def __init__(self, name, **kwargs):
		super(ProcMetric,self).__init__(name)
		self.kwargs = kwargs
		self.kwargs['name'] = name
		try:
			self.keys = kwargs['keys'].strip().split(',')
		except (ValueError, KeyError):
			self.keys = ['user-cpu','sys-cpu','real-mem','virt-mem','files','children','connections','percent-mem','threads']
		self.attrs = {
			'user-cpu'    : (ProcMetric.userCPU, 'Seconds'),
			'sys-cpu'     : (ProcMetric.sysCPU , 'Seconds'),
			'real-mem'    : (ProcMetric.realMem, 'Megabytes'),
			'virt-mem'    : (ProcMetric.virtMem, 'Megabytes'),
			'files'       : (ProcMetric.numFiles, 'Count'),
			'children'    : (ProcMetric.numChildren, 'Count'),
			'connections' : (ProcMetric.numConnections, 'Count'),
			'uptime'      : (ProcMetric.uptime, 'Seconds'),
			'percent-mem' : (psutil.Process.get_memory_percent, 'Percent'),
			'threads'     : (psutil.Process.get_num_threads, 'Count')
		}

	@staticmethod
	def userCPU(p):
		return p.get_cpu_times()[0]
	
	@staticmethod
	def sysCPU(p):
		return p.get_cpu_times()[1]
	
	@staticmethod
	def realMem(p):
		return p.get_memory_info()[0] / (1024.0 ** 2)
	
	@staticmethod
	def virtMem(p):
		return p.get_memory_info()[1] / (1024.0 ** 2)
	
	@staticmethod
	def numChildren(p):
		return len(p.get_children())
	
	@staticmethod
	def numFiles(p):
		return len(p.get_open_files())
	
	@staticmethod
	def numConnections(p):
		return len(p.get_connections())
	
	@staticmethod
	def uptime(p):
		return (time.time() - p.create_time)
	
	def match(self, p):
		try:
			for key,value in self.kwargs.items():
				if key == 'name':
					if not re.search(value, p.name):
						return False
				if key == 'user':
					if not re.search(value, p.username):
						return False
				if key == 'args':
					if not re.search(value, ' '.join(p.cmdline)):
						return False
				if key == 'cwd':
					if not re.search(value, p.getcwd()):
						return False
			return True
		except psutil.error.AccessDenied:
			return False
	
	def values(self):
		try:
			results = {}
			count = 0
			for p in psutil.process_iter():
				if self.match(p):
					count += 1
					for key in self.keys:
						attr = self.attrs[key]
						r = attr[0](p)
						try:
							results[key][0] += r
						except Exception:
							results[key] = [r, attr[1]]
			results['count'] = (count, 'Count')
			return {'results': dict((k, tuple(v)) for k,v in results.items())}
		except KeyError:
			return {'error': 'Could not find all keys in searchd status'}
