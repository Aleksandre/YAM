"""
Calling this module puts up a server able to
process incoming request, keep track of known devices 
and broadcast it's presence to other devices.

For now, the server only handles music playback requests.

TL:DR
This is an audio player controlled remotely via TCP commands
"""

import threading
from player import LocalPlayer
import socket
import sys
import config
from networking import RemoteClient, EchoRequestHandler, YamRequestHandler, RequestServer, DeviceStateMulticaster, NetworkInterfaceWatcher
from devices import DevicePresenceBroadcaster, Device, DeviceWatcher


class ServerApp():
    def __init__(self, tcpServer, player = None, device = None, playerStateBroadcaster = None, networkIFaceWatcher=None):
        self.tcpServer = tcpServer
        self.presenceBroadcaster = DevicePresenceBroadcaster(device)
        self.player = player
        self.device = device
        self.playerStateBroadcaster = playerStateBroadcaster
        self.networkIFaceWatcher = networkIFaceWatcher
        self.bindEvents()

    def start(self):
        self.tcpServer.start()
        self.presenceBroadcaster.start()
        self.player.start()
        
        if self.networkIFaceWatcher:
            self.networkIFaceWatcher.start()

    def bindEvents(self):
        if self.player:
            self.player.ticked.connect(self._playerTicked)
            self.player.stateChanged.connect(self._playerStateChanged)
            self.player.sourceChanged.connect(self._playerStateChanged)
    
    def stop(self):
        self.tcpServer.stop()
        self.presenceBroadcaster.stop()
        self.networkIFaceWatcher.stop()
        self.player.exit()

    def _playerStateChanged(self):
        print "Player state is: {0}".format(self.player.getState())
        if self.playerStateBroadcaster:
            self.playerStateBroadcaster.sendState()

    def _playerTicked(self, currentTimeMS):
        pass

def setupTestServer():
    player = LocalPlayer()
    player.setHeadless()

    server = RequestServer(player=player)
    ip, port = server.server_address

    thisDevice = Device(type="local", visibleName="rpi-testyamserver", url="{0}:{1}".format(ip,port))

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


def assembleServer(host, port):
    player = LocalPlayer()
    player.setHeadless()
    server = RequestServer((host,port), player=player)
    thisDevice = Device(type="local", visibleName="rpi-yamserver", url="{0}:{1}".format(host,port))
    stateBroadcaster = DeviceStateMulticaster(player) 
    networkIFaceWatcher = NetworkInterfaceWatcher(delayInSec=5)
    networkIFaceWatcher.start()
    return ServerApp(server, player, thisDevice, stateBroadcaster, networkIFaceWatcher)

def main():

    HOST = socket.gethostname()
    if len(sys.argv) > 1:
        HOST = sys.argv[1]
    
    PORT = 5005
    if len(sys.argv) > 2:
        PORT = int(sys.argv[2])
    
    config.setConfigFolder('../config/')
    server = assembleServer(HOST, PORT)
    try:
        server.start()
    except KeyboardInterrupt:
        print "Received keypress. Stopping the server."
        server.stop()

if __name__ == '__main__':
    sys.exit(main())
    




