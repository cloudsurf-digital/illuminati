#! /usr/bin/env python
# 
# Copyright (c) 2011 SEOmoz
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import socket
import hashlib
import threading
from sauron import logger
from twisted.internet import reactor
from twisted.words.xish import domish
from twisted.names.srvconnect import SRVConnector
from sauron.emitters import Emitter, EmitterException
from twisted.words.protocols.jabber import xmlstream, client, jid

class XMPPClientConnector(SRVConnector):
    def __init__(self, reactor, domain, factory):
        SRVConnector.__init__(self, reactor, 'xmpp-client', domain, factory)
    
    def pickServer(self):
        host, port = SRVConnector.pickServer(self)
        if not self.servers and not self.orderedServers:
            port = 5222
        return host, port

class JabberBot(Emitter):
    def __init__(self, user, password, host=None, port=5222, resource=None):
        self.xmlstream = None
        self.user, self.host = user.split('@')
        self.server = host or self.host
        self.resource = resource or socket.gethostname()
        self.jid = jid.JID(tuple=(self.user, self.host, self.resource))
        self.full = self.jid.full()
        self.cids = {}
        factory = client.XMPPClientFactory(self.jid, password)
        factory.addBootstrap(xmlstream.STREAM_CONNECTED_EVENT, self.connected)
        factory.addBootstrap(xmlstream.STREAM_END_EVENT, self.disconnected)
        factory.addBootstrap(xmlstream.STREAM_AUTHD_EVENT, self.authenticated)
        factory.addBootstrap(xmlstream.INIT_FAILED_EVENT, self.init_failed)
        factory.addBootstrap('/iq/bind/jid', self.bind)
        logger.info('Connecting %s' % str(self))
        reactor.connectTCP(self.server, 5222, factory)

    def __del__(self):
        try:
            self.xmlstream.sendFooter()
        except:
            logger.exception('Problem during delete')

    def __str__(self):
        return self.full
    
    def bind(self, msg):
        '''Yeah, this is ugly as sin, but Element doesn't support xpath'''
        for e in msg.elements():
            if e.name == 'bind':
                for e in e.elements():
                    if e.name == 'jid':
                        self.full = str(e)
                        logger.info(self.full)
                        return

    def connected(self, xs):
        logger.info('Connected %s' % str(self))
        self.xmlstream = xs
    
    def disconnected(self, xs):
        logger.info('Disconnected %s' % str(self))
    
    def authenticated(self, xs):
        logger.info('Authenticated %s' % str(self))
        self.xmlstream.addObserver('/message', self.message)
        self.xmlstream.addObserver('/presence', self.presence)
        self.xmlstream.addObserver('/iq', self.iq)
        self.xmlstream.addObserver('/*', self.all)
        presence = domish.Element((None, 'presence'))
        self.xmlstream.send(presence)
        msg = domish.Element(('jabber:client', 'message'))
        msg['from'] = str(self)
        msg['to'] = 'dan.lecocq@kaust.edu.sa'
        msg['type'] = 'chat'
        msg.addElement('body', 'jabber:client', 'testing')
        html = domish.Element((None, 'html'))
        html['xmlns'] = 'http://jabber.org/protocol/xhtml-im'
        body = domish.Element((None, 'body'))
        body['xmlns'] = 'http://www.w3.org/1999/xhtml'
        img = domish.Element((None, 'img'))
        # The hash should be of the data you send across
        data = open("seomoz.png", "rb").read().encode('base64')
        key  = 'sha1+%s@bob.xmpp.org' % hashlib.sha1(data.replace('\n', '')).hexdigest()
        self.cids[key] = data
        img['src'] = 'cid:%s' % key
        img['alt'] = 'seomoz'
        body.addChild(img)
        html.addChild(body)
        msg.addChild(html)
        logger.warn(self.msgToString(msg))
        self.xmlstream.send(msg)
        
    def init_failed(self, failure):
        logger.warn('Initialization failed %s : %s' % (str(self), failure.getErrorMessage()))
    
    def send(self, to, message, subject=None, type='chat'):
        msg = domish.Element(('jabber:client', 'message'))
        msg['from'] = str(self)
        msg['to'] = to
        msg['type'] = type
        msg.addElement('body', 'jabber:client', message)
        if subject:
            msg.addElement('subject', 'jabber:client', subject)
        self.xmlstream.send(msg)
        logger.info('Sent %s message %s' % (to, message))
    
    def msgToString(self, msg):
        return msg.toXml().replace('><', '>\n\t<').replace('\' ', '\'\n\t\t').replace('" ', '"\n\t\t')
    
    def error(self, msg):
        logger.error('Received error %s' % self.msgToString(msg))
        
    def chat(self, msg):
        logger.info('Received message %s' % self.msgToString(msg))
        self.send(msg['from'], 'hello')

    def message(self, msg):
        try:
            if msg['type'] == 'chat':
                self.chat(msg)
            elif msg['type'] == 'error':
                self.error(msg)
            else:
                logger.error('Unknown message type: %s' % self.msgToString(msg))
        except:
            logger.exception('Failed to parse message')

    def all(self, msg):
        #logger.info(self.msgToString(msg))
        pass
    
    def iq(self, iq):
        logger.info(self.msgToString(iq))
        if iq['type'] == 'get':
            cid = None
            for e in iq.elements():
                try:
                    cid = e['cid']
                    break
                except KeyError:
                    continue
            if cid:
                response = domish.Element((None, 'iq'))
                response['id'] = iq['id']
                response['to'] = iq['from']
                response['type'] = 'result'
                data = domish.Element(('urn:xmpp:bob', 'data'))
                data['cid'] = cid
                data['type'] = 'image/png'
                data['max-age'] = '86400'
                data.addContent('\n')
                data.addContent(self.cids[cid])
                response.addChild(data)
                logger.info('Sending %s' % self.msgToString(response))
                self.xmlstream.send(iq)
    
    def presence(self, presence):
        pass
        
    def metrics(self, metrics):
        self.results = metrics