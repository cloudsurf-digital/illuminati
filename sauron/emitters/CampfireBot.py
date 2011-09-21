#! /usr/bin/env python

import Emitter
import logging
import threading
from pinder import Campfire
from twisted.internet import reactor

logger = logging.getLogger('sauron')

class CampfireBot(Emitter.Emitter):
	def __init__(self, subdomain, token):
		super(Emitter.Emitter,self).__init__()
		logger.info('Making Campfire...')
		self.camp = Campfire(subdomain, token)
		logger.info('Rooms...')
		self.rooms = {}
		logger.info('Room...')
		self.camp.find_room_by_name('Testing').join()
		self.results = {}
		try:
			threading.Thread(target=reactor.run).start()
		except Exception:
			pass

	def message(msg):
		if not msg['body'].find('sauron'):
			try:
				self.rooms[msg['room_id']].speak(repr(self.metrics))
			except KeyError:
				self.rooms[msg['room_id']] = self.camp.room(msg['room_id'])
		logger.info(repr(msg))
	
	def err(msg):
		logger.error(repr(msg))
	
	def metrics(self, metrics):
		self.results = metrics
	