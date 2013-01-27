
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.


from twisted.internet import reactor, protocol
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet import defer, protocol
import atexit
import sys

"""
Server components
"""

server = None
client = None

@atexit.register
def tearDown():
    print "Tearing down endpoint..."
    global server, clientConnexion

    if server: 
        print "Stopping server."
        server.stopListening()
    if client:  
        print "Stopping client."
        client.disconnect()
    if reactor.running:
        reactor.stop()

class Echo(protocol.Protocol):
    
    def dataReceived(self, data):
        print "Server received a request: {0}".format(data)
        self.transport.write(data)

        if data == "STOP":
            self.stop()
            self.transport.write(data)

    def stop(self):
        print "Stopping server..."
        reactor.stop()


"""
Client components
"""

class EchoClient(protocol.Protocol):
    """
    An example client. Run simpleserv.py first before running this.
    """

    def connectionMade(self):
        print "Connexion established with server."
    
    def dataReceived(self, data):
        print "Client received data from server: {0}".format(data)
    
    def connectionLost(self, reason):
        print "Client connection lost: {0}".format(0)

    def sendMessage(self, msg):
        print "Client is sending data to server"
        self.transport.write(msg)

class EchoFactory(protocol.ClientFactory):
    protocol = EchoClient

    def clientConnectionFailed(self, connector, reason):
        print "Client connection failed."
        reactor.stop()
    
    def clientConnectionLost(self, connector, reason):
        print "Client connection lost."
        reactor.stop()


def runServer():
    factory = protocol.ServerFactory()
    factory.protocol = Echo

    global server
    server = reactor.listenTCP(5005, factory)
    reactor.run()

def runTests():
    import threading
    serverThread = threading.Thread(target=runServer)
    serverThread.start()

    clientThread = threading.Thread(target=runClient)
    clientThread.start()

def onConnected(protocol):
    print "Client is connected to server."
    protocol.sendMessage("STOP")
    global reactor
    reactor.stop()

def runClient():
    # this connects the protocol to a server runing on port 8000
    client = TCP4ClientEndpoint(reactor, "localhost", 5005)
    d = client.connect(EchoFactory())
    d.addCallback(onConnected)
    reactor.run()

if __name__ == '__main__':
    mode = sys.argv[1]
    print "Running with mode: {0}".format(mode)

    if mode == 'cli':
        runClient()
    elif mode == 'ser':
        runServer()
    elif mode == 'test':
        runTests()


