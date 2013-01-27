"""
Calling this module puts up a server able to
process incoming request, keep track of known devices 
and broadcast it's presence to other devices.

For now, the server only handles music playback requests.

TL:DR
This is an audio player controlled remotely via TCP commands
"""

from socket import *
import threading
from player import LocalPlayer, RemoteClient
from content import Mock
import socket
from devices import DevicePresenceBroadcaster, Device
import sys
import SocketServer



ERRORS = ["[1] The specified controller '{0}' method could not be found.\n",
          "[2] The specified method '{0}' could not be handled by the controller.\n"]

class EchoRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        print "Server received request..."
        request = data = self.request.recv(4096)
        while not data.endswith("\n"): 
            data = self.request.recv(4096)
            request = request + data
        print "Handling request: {0}".format(request)
        self.request.sendall(request)

class YamRequestHandler(SocketServer.BaseRequestHandler):
    
    def handle(self):
        print "Server received request..."
        request = data = self.request.recv(4096)
        while not data.endswith("\n"): 
            data = self.request.recv(4096)
            request = request + data
        print "Handling request: {0}".format(request)
        self.handleRequest(data, self.server)

    def handleRequest(self, requestData, server):
        """
        Default request handler.
        You can inject one using the constuctor.

        Expecting requestData like: '1;2;3'
        where 1 is target (controller)
              2 is method (function to call)
              3 is data (Optionnal)

        Example: player;playTrack;{a content.Track object}

        For now, only 'player' (see player.py) is availaible as a controller
        """
        print requestData
        args = requestData.split(';')

        controllerName = args[0].strip()
        method = args[1].strip()   

        controller = server.player

        if controllerName == None:
            print "Could not find the specified controller: {0}".format(controllerName)
            self.request.sendall(ERRORS[0].format(controllerName))

        if not hasattr(controller, method):
            print "Could not find the specified method: {0}".format(method)
            self.request.sendall(ERRORS[1].format(method))

        #Call controller method
        if len(args) >= 3:
            #It got args
            data = args[2].strip()
            method = getattr(controller, method)
            if method:
                print "Calling controller method with arguments..."
                #Call the target method on the specified controller
                self.request.sendall(str(method(self.castStrToDict(data))) + "\n")
            else:
                print "The method '{0}'' is not availaible on the specified controller.".format(method)
        else:
            print "Calling controller method without arguments..."
            self.request.sendall(str(getattr(controller, method)()) + "\n")

    def castStrToDict(self, strValue):
        """
        Parse the string received via UDP to a mock object
        """
        try:
            result = eval(strValue)
            requestObject = Mock()
            requestObject.__dict__ = result
            return requestObject
        except:
            pass
        try:
            #print strValue
            arrayOfDict = []
            result = strValue.split('|')
            for arg in result:
                arrayOfDict.append(self.castStrToDict(arg))
            return arrayOfDict
        except:
            pass

class RequestServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    
    def __init__(self, server_address = ('localhost', 0), handler_class=YamRequestHandler, player = None):
        SocketServer.TCPServer.__init__(self, server_address, handler_class, bind_and_activate=False)
        #Attribute necessery to be accessed from YamRequetHandler instance
        self.player = player

    def start(self, name="RequestServer"):   
        "Starting RequestServer..."
        self.allow_reuse_address = True # Prevent 'cannot bind to address' errors on restart
        self.server_bind()     # Manually bind, to support allow_reuse_address
        self.server_activate() # (see above comment)
        self.t = threading.Thread(target=self.serve_forever, name=name)
        self.t.start()

    def stop(self):
        print "Stopping RequestServer..."
        self.isRunning=False
        self.socket.close()
        self.shutdown()
        print "RequestServer stopped."

    def getProcName(self):
        return self.t.name

class ServerApp():
    def __init__(self, tcpServer, player = None, device = None):
        self.tcpServer = tcpServer
        self.presenceBroadcaster = DevicePresenceBroadcaster(device)
        self.player = player
        self.device = device

    def start(self):
        self.tcpServer.start()
        self.presenceBroadcaster.start()
        self.player.start()

    def stop(self):
        self.tcpServer.stop()
        self.presenceBroadcaster.stop()
        #self.player.exit()

def setupTestServer():
    player = LocalPlayer()
    player.setHeadless()

    server = RequestServer(player=player)
    ip, port = server.server_address

    thisDevice = Device(type="local", visibleName="rpi-testyamserver", url="{0}:{1}".format(ip,port))

    return ServerApp(server, player, thisDevice)

def setupServer():
    player = LocalPlayer()
    player.setHeadless()
    host, port = socket.gethostname(), 5000
    server = RequestServer((host,port), player=player)
    thisDevice = Device(type="local", visibleName="rpi-yamserver", url="{0}:{1}".format(host,port))

    return ServerApp(server, player, thisDevice)


def testServerAndPlayerIntegration():
    host, port = 'localhost', 5000
    server = RequestServer((host, port), player=LocalPlayer(), handler_class=YamRequestHandler)
    server.start()

    client = RemoteClient(host, port)
    client.sendRequest('player;getState')
    
    server.stop()

def testClientAndServer():
    host, port = 'localhost', 5000
    server = RequestServer((host, port), handler_class=EchoRequestHandler)
    server.start()

    client = RemoteClient(host, port)
    client.sendRequest('HELLO WORLD')

    import time
    time.sleep(1)
    client.sendRequest('Second message')
    
    server.stop()
    return 0

def testServerApp():
    player = LocalPlayer()
    player.setHeadless()

    requestServer = RequestServer(player=player)
    ip, port = server.server_address

    thisDevice = Device(type="local", visibleName="rpi-yamserver", url="{0}:{1}".format(ip,port))

    app = ServerApp(requestServer, player, thisDevice)
    app.start()


def main():
    server = setupServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print "Received keypress. Stopping the server."
        server.stop()


if __name__ == '__main__':
    sys.exit(main())
    




