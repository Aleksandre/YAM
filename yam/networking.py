from socket import *
import threading
import socket
import SocketServer
from content import Mock
import sys
import re
import socket
import subprocess
import time

class RemoteClient():
    """
    The RemoteClient sends commands to a remote DeviceRequestListener via TCP.
    """
    def __init__(self, host, port, callback = None, name="reqsender"):
        print "Remote client initiated with url: {0}:{1}".format(host, port)
        self.tcpIP = host
        self.tcpPort = int(port)
        self.bufferSize = 25000
        self.name = name
        self.callback = callback

    def printInfo(self):
        print "Targeting: {0}:{1}".format(self.tcpIP,self.tcpPort)

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.settimeout(7.0)
        print "Connecting to {0}:{1}".format(self.tcpIP,self.tcpPort)
        self.sock.connect((self.tcpIP, self.tcpPort))
        print "Connected."

    def sendRequest(self, request):
        self.connect()
        print "Sending request: {0}".format(request)
        answer = None
        try:
            self.sock.sendall(request + "\n")
            answer = data = self.sock.recv(4096)
            print "Receiving data from server: {0}".format(answer)
            while not data.endswith("\n"):
                data = self.sock.recv(4096)
                answer = answer + data
            print "Got complete answer from server: {0}".format(answer)
        except IOError as e:
            print e

        #if self.callback:
           # self.callback(answer)
        self.disconnect()
        return answer

    def disconnect(self):
        print "Disconnecting from server..."
        self.sock.close()



ERRORS = ["[1] The specified controller '{0}' method could not be found.\n",
          "[2] The specified method '{0}' could not be handled by the controller.\n",
          "[3] Could not parse the request. At least 2 arguments are necessary.\n"]

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
        self.handleRequest(request, self.server)

    def handleRequest(self, requestData, server):
        """
        Default request handler.
        You can inject one using the constuctor.

        Expecting requestData like: '1;2;3'
        where 1 is target (controller)
              2 is method (function to call)
              3 is data (Optionnal)

        Example: player;playTrack;{a content.Track object | Another Track | Yet another track}

        For now, only 'LocalPlayer' (see player.py) is availaible as a controller
        """
        args = requestData.strip().split(';')
        if len(args) < 2:
            print "Could not parse request (not enough args): {0}".format(args)
            self.request.sendall(ERRORS[2])
            return

        controllerName = args[0].strip()
        method = args[1].strip()

        if controllerName == None:
            print "Could not find the specified controller: {0}".format(controllerName)
            self.request.sendall(ERRORS[0].format(controllerName))
            return

        if controllerName == "player":
        	controller = server.player
        elif controllerName == "content":
            controller = server.contentProvider

        if not hasattr(controller, method):
            print "Could not find the specified method: {0}".format(method)
            self.request.sendall(ERRORS[1].format(method))
            return

        #Call controller method
        if len(args) >= 3:
            #It got args
            data = args[2].strip()
            method = getattr(controller, method)
            if method:
                print "Calling controller method with arguments..."
                #Call the target method on the specified controller
                if '{' in data:
					data = self.castStrToDict(data)
                self.request.sendall(str(method(data)) + "\n")
            else:
                print "The method '{0}' is not availaible on the specified controller.".format(method)
        else:
            print "Calling controller method without arguments..."
            self.request.sendall(str(getattr(controller, method)()) + "\n")

    def castStrToDict(self, strValue):
        """
        Parse the string received to a mock object
        """
        try:
            result = eval(strValue)
            requestObject = Mock(result)
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

class DeviceStateMulticaster():
    """
    Notify registered devices when the state of a player changes.
    """
    def __init__(self, player, portToTarget = 5556):
        self.port = portToTarget or config.getProperty("player_state_multicast_target_port")
        self.sock = socket.socket(AF_INET, SOCK_DGRAM)
        self.sock.bind(('', 0))
        self.sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
       	self.player = player

    def sendState(self):
    	self.thread = threading.Thread(target=self._run, name="player_state_bc")
    	if not self.thread.is_alive():
	        print "Notifying interested hosts of player state..."
	        self.thread.start()

    def _run(self):
    	state = self.player.getFullState()
    	for host in self.player.hostsInterestedByState:
	        try:
	        	print "Sending player state to host: {0} on port {1}".format(host, self.port)
	        	self.sock.sendto(str(state), (host, int(self.port)))
	        except Exception as e:
	            print e
