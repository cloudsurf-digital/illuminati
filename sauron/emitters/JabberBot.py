#! /usr/bin/env python

import socket
import logging
import Emitter
import threading
from twisted.internet import reactor
from twisted.words.xish import domish
from twisted.words.protocols.jabber import xmlstream, client, jid

class JabberBot(Emitter.Emitter):
	def __init__(self, user, host, password, port=5222, location=None):
		self.xmlstream = None
		self.user = user
		self.host = host
		self.location = location or socket.gethostname()
		self.jid = jid.JID('%s@%s/%s' % (self.user, self.host, self.location))
		factory = client.XMPPClientFactory(self.jid, password)
		factory.addBootstrap(xmlstream.STREAM_CONNECTED_EVENT, self.connected)
		factory.addBootstrap(xmlstream.STREAM_END_EVENT, self.disconnected)
		factory.addBootstrap(xmlstream.STREAM_AUTHD_EVENT, self.authenticated)
		factory.addBootstrap(xmlstream.INIT_FAILED_EVENT, self.init_failed)
		Emitter.logger.info('Connecting %s' % str(self))
		reactor.connectTCP(host, port, factory)

	def __del__(self):
		self.xmlstream.sendFooter()

	def __str__(self):
		return '%s@%s/%s' % (self.user, self.host, self.location)

	def connected(self, xs):
		Emitter.logger.info('Connected %s' % str(self))
		self.xmlstream = xs
	
	def disconnected(self, xs):
		Emitter.logger.info('Disconnected %s' % str(self))
	
	def authenticated(self, xs):
		Emitter.logger.info('Authenticated %s' % str(self))
		presence = domish.Element((None, 'presence'))
		self.xmlstream.send(presence)
	
	def init_failed(self):
		Emitter.logger.warn('Initialization failed %s' % str(self))

	def message(self, msg):
		response = domish.Element(('jabber:client', 'message'))
		response['to'] = msg['from']
		response['from'] = str(self)
		response['type'] = 'chat'
		response.addElement('body', 'jabber:client', 'hello')
		
	def metrics(self, metrics):
		self.results = metrics