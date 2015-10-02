from twisted.internet import defer
from twisted.internet.protocol import ServerFactory, ClientFactory
from twisted.internet import reactor
from sauron.utils.jsonrpc2 import JsonRPCProtocol

class EchoClient(ClientFactory):
  class protocol(JsonRPCProtocol):
    end = 'Goodbye!'
    def connectionMade(self):
      @defer.inlineCallbacks
      def runall():
        res = yield self.callRemote('echo','Hello, world!')
        print self.factory.__class__.__name__,'receive:',res
        res = yield self.echo('What a fine day it is.')
        print self.factory.__class__.__name__,'receive:',res
        res = yield self.echo('Who?','What?','When?','Where?','Why?','How?')
        print self.factory.__class__.__name__,'receive:',res
        res = yield self.bounce('Call me back!')
        defer.returnValue(None)
      def callback(res):
        self.beginQueue().bounce.notify('Bounce!').bounce.notify(self.end).endQueue()
        runall().addCallback(callback)
    def connectionLost(self,reason):
      print 'connection lost (protocol)'
    def jsonrpc_echo(self,*args):
      largs = len(args)
      if largs == 1:
        print self.factory.__class__.__name__,'receive:',args[0]
        if args[0] == self.end:
          self.transport.loseConnection()
        return args[0]
      elif largs > 1:
        print self.factory.__class__.__name__,'receive:',args
        return args
  def clientConnectionFailed(self,connector,reason):
    print 'connection failed:',reason.getErrorMessage()
    reactor.stop()
  def clientConnectionLost(self,connector,reason):
    print 'connection lost:',reason.getErrorMessage()
    reactor.stop()

reactor.connectUNIX('/var/tmp/ext-sauron.sock', EchoClient())
reactor.run()
