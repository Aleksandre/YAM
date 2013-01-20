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
from player import LocalPlayer
from content import Mock
import socket
from devices import DeviceManager, DevicePresenceBroadcaster, Device
import sys
import SocketServer

class YamRequestHandler(SocketServer.BaseRequestHandler):
    
    def handle(self):
        # Echo the back to the client
        data = self.request.recv(20000)
        print "Handling request: {0}".format(data)
        self.handleRequest(data, self.server)
        return

    def handleRequest(self, requestData, server):
        """
        Default request handler.
        You can inject one using the constuctor.

        Expecting requestData like: '1;2;3'
        where 1 is target (controller)
              2 is method (function to call)
              3 is data (Optionnal)

        Example: [player;playTrack;{a content.Track object}]

        For now, only 'player' (see player.py) is availaible as a controller
        """
        print "Handling remote request..."
        
        args = requestData.split(';')

        controllerName = args[0].strip()
        method = args[1].strip()   

        controller = server.player

        if controllerName == None:
            print "Could not find the specified controller: {0}".format(controllerName)

        #Call controller method
        if len(args) >= 3:
            #It got args
            data = args[2].strip()
            method = getattr(controller, method)
            if method:
                print "Calling controller method with arguments..."
                #Call the target method on the specified controller
                self.request.send(method(self.castStrToDict(data)))
            else:
                print "The method '{0}'' is not availaible on the specified controller.".format(method)
        else:
            print "Calling controller method without arguments..."
            self.request.send(getattr(controller, method)())

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
            result = strValue[1:-1].split('|')
            for arg in result:
                arrayOfDict.append(self.castStrToDict(arg))
            return arrayOfDict
        except:
            pass

class YamTcpServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    
    def __init__(self, server_address = ('localhost', 0), handler_class=YamRequestHandler, player = None):
        SocketServer.TCPServer.__init__(self, server_address, handler_class)
        self.player = player

    def start(self, name="yamtcpserver"):   
        self.t = threading.Thread(target=self._run, name=name)
        self.t.setDaemon(True) # don't hang on exit
        self.t.start()

    def stop(self):
        self.socket.close()

    def getProcName(self):
        return self.t.name

    def _run(self):
        while True:
            self.handle_request()
        return


    def server_activate(self):
        SocketServer.TCPServer.server_activate(self)
        return
    def verify_request(self, request, client_address):
        return SocketServer.TCPServer.verify_request(self, request, client_address)

    def process_request(self, request, client_address):
        return SocketServer.TCPServer.process_request(self, request, client_address)

    def server_close(self):
        return SocketServer.TCPServer.server_close(self)

    def finish_request(self, request, client_address):
        return SocketServer.TCPServer.finish_request(self, request, client_address)

    def close_request(self, request_address):
        return SocketServer.TCPServer.close_request(self, request_address)

class ServerApp():
    def __init__(self, tcpServer, player, device):
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
        self.player.exit()


def setupTestServer():
    player = LocalPlayer()
    player.setHeadless()

    server = YamTcpServer(player=player)
    ip, port = server.server_address

    thisDevice = Device(type="local", visibleName="rpi-testyamserver", url="{0}:{1}".format(ip,port))

    return ServerApp(server, player, thisDevice)

def setupServer():
    player = LocalPlayer()
    player.setHeadless()

    server = YamTcpServer(player=player)
    ip, port = server.server_address
    thisDevice = Device(type="local", visibleName="rpi-yamserver", url="{0}:{1}".format(ip,port))

    return ServerApp(server, player, thisDevice)

def main():
    server = setupServer()
    server.start()

if __name__ == '__main__':
    sys.exit(main())
    




