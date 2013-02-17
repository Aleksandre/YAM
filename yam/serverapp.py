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
from networking import RemoteClient, EchoRequestHandler, YamRequestHandler, RequestServer, DeviceStateMulticaster
from devices import DevicePresenceBroadcaster, Device, DeviceWatcher
from optparse import OptionParser
import devices

class ServerApp():
    def __init__(self, tcpServer, player = None, presenceBroadcaster=None, playerStateBroadcaster = None):
        self.tcpServer = tcpServer
        self.player = player
        self.presenceBroadcaster = presenceBroadcaster
        self.playerStateBroadcaster = playerStateBroadcaster
        self.bindEvents()

    def start(self):
        print "Starting tcp server on: {0}".format(self.tcpServer.server_address)
        self.tcpServer.start()
        self.presenceBroadcaster.start()
        self.player.start()

    def bindEvents(self):
        if self.player:
            self.player.ticked.connect(self._playerTicked)
            self.player.stateChanged.connect(self._playerStateChanged)
            self.player.sourceChanged.connect(self._playerStateChanged)

    def stop(self):
        print "Stopping server..."
        self.tcpServer.stop()
        self.presenceBroadcaster.stop()
        self.player.exit()
        print "Server stopped..."

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


def assembleServer(host, port, broadcast_port):
    #init player
    player = LocalPlayer()
    player.setHeadless()

    #init the request server
    server = RequestServer((host,port), player=player)

    #init device
    thisDevice = Device(type="local", visibleName="rpi-yamserver", url="{0}:{1}".format(host,port))
    thisDevice.setCapabilities([devices.Capability.PlayMusic])

    #init presence broadcaster
    presenceBroadcaster = DevicePresenceBroadcaster(thisDevice, broadcast_port)

    #init state broadcaster
    stateBroadcaster = DeviceStateMulticaster(player)

    #assemble and return the server
    return ServerApp(server, player, presenceBroadcaster, stateBroadcaster)

def main():

    parser = OptionParser()
    parser.add_option("-a", "--address", dest="host", action="store", default=socket.gethostname(), type="str", help="the address or host name on which the server is listening")
    parser.add_option("-p", "--request_port",
                      action="store", dest="request_port", default=5005, type="int",
                      help="the port number on which the server is listening for tcp requests.")
    parser.add_option("-w", "--workspace",
                      action="store", dest="workspace", default='../config/', type="str",
                      help="the server workspace location.")
    parser.add_option("-b", "--broadcast_port",
                      action="store", dest="broadcast_port", default='5555', type="int",
                      help="the port on which the server is broadcasting it's presence.")

    options, args = parser.parse_args()

    HOST = options.host
    PORT = options.request_port
    TARGET_PORT = options.broadcast_port
    WORKSPACE = options.workspace

    config.setWorkspaceLocation(WORKSPACE)
    server = assembleServer(HOST, PORT, TARGET_PORT)

    try:
        server.start()
    except KeyboardInterrupt:
        print "The server received a keypress event. Stopping the server."
    except Exception as ex:
        print "The server encountered an unexpected exception: {0}".format(ex)
    finally:
        server.stop()

if __name__ == '__main__':
    sys.exit(main())





