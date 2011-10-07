#! /usr/bin/env python

import socket
import logging
import Emitter
import threading
from twisted.internet import reactor
from twisted.words.xish import domish
from twisted.names.srvconnect import SRVConnector
from twisted.words.protocols.jabber import xmlstream, client, jid

class XMPPClientConnector(SRVConnector):
	def __init__(self, reactor, domain, factory):
		SRVConnector.__init__(self, reactor, 'xmpp-client', domain, factory)
	
	def pickServer(self):
		host, port = SRVConnector.pickServer(self)
		if not self.servers and not self.orderedServers:
			port = 5222
		return host, port

class JabberBot(Emitter.Emitter):
	def __init__(self, user, password, host=None, port=5222, resource=None):
		self.xmlstream = None
		self.user, self.host = user.split('@')
		self.server = host or self.host
		self.resource = resource or socket.gethostname()
		self.jid = jid.JID(tuple=(self.user, self.host, self.resource))
		factory = client.XMPPClientFactory(self.jid, password)
		factory.addBootstrap(xmlstream.STREAM_CONNECTED_EVENT, self.connected)
		factory.addBootstrap(xmlstream.STREAM_END_EVENT, self.disconnected)
		factory.addBootstrap(xmlstream.STREAM_AUTHD_EVENT, self.authenticated)
		factory.addBootstrap(xmlstream.INIT_FAILED_EVENT, self.init_failed)
		Emitter.logger.info('Connecting %s' % str(self))
		reactor.connectTCP(self.server, 5222, factory)

	def __del__(self):
		try:
			self.xmlstream.sendFooter()
		except:
			Emitter.logger.exception('Problem during delete')

	def __str__(self):
		return self.jid.full()

	def connected(self, xs):
		Emitter.logger.info('Connected %s' % str(self))
		self.xmlstream = xs
	
	def disconnected(self, xs):
		Emitter.logger.info('Disconnected %s' % str(self))
	
	def authenticated(self, xs):
		Emitter.logger.info('Authenticated %s' % str(self))
		self.xmlstream.addObserver('/message', self.message)
		self.xmlstream.addObserver('/presence', self.presence)
		self.xmlstream.addObserver('/iq', self.iq)
		presence = domish.Element((None, 'presence'))
		self.xmlstream.send(presence)
	
	def init_failed(self, failure):
		Emitter.logger.warn('Initialization failed %s : %s' % (str(self), failure.getErrorMessage()))
	
	def send(self, to, message, subject=None, type='chat'):
		msg = domish.Element(('jabber:client', 'message'))
		msg['to'] = to
		msg['type'] = type
		msg.addElement('body', 'jabber:client', message)
		if subject:
			msg.addElement('subject', 'jabber:client', subject)
		self.xmlstream.send(msg)
		Emitter.logger.info('Sent %s message %s' % (to, message))
	
	def error(self, msg):
		Emitter.logger.error('Received error %s' % msg.toXml())
		
	def chat(self, msg):
		Emitter.logger.info('Received message %s' % msg.toXml())
		self.send(msg['from'], 'hello')

	def message(self, msg):
		try:
			if msg['type'] == 'chat':
				self.chat(msg)
			elif msg['type'] == 'error':
				self.error(msg)
			else:
				Emitter.logger.error('Unknown message type: %s' % msg.toXml())
		except:
			Emitter.logger.exception('Failed to parse message')
	
	def iq(self, iq):
		pass
	
	def presence(self, presence):
		pass
		
	def metrics(self, metrics):
		self.results = metrics