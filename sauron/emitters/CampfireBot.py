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

import threading
from sauron import logger
from pinder import Campfire
from twisted.internet import reactor
from sauron.emitters import Emitter, EmitterException

class CampfireBot(Emitter):
    def __init__(self, subdomain, token):
        super(Emitter,self).__init__()
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
    
