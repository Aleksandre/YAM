"""
Calling this module puts up a server able to
process incoming request, keep track of known device 
and broadcast it's presence to other devices.

For now, the server only handles and music playback requests.

TL:DR
This is a vlc player controlled remotely via tcp commands
"""

from socket import *
import threading
from player import LocalPlayer
import Queue
from content import Mock
import time
import socket
from devices import DeviceManager, DevicePresenceBroadcaster
import select
import sys

PLAYER = LocalPlayer()
PLAYER.setHeadless()

#Holds requests received via the DeviceRequestListener
requests = Queue.Queue()

class DeviceRequestListener:
    """
    The DeviceRequestListener binds to a PORT and listens to TCP requests.
    When a request is received, add it to the request queue.
    """
    def __init__(self):
        self.running = False
        self.thread = threading.Thread(target=self._run)

    def start(self):
        self.thread.start()

    def stop(self):
        print "Stopping  DeviceRequestListener..."
        self.running = False
        self._close()
        print "Stopped DeviceRequestListener."

    def _run(self):
        TCP_IP = '127.0.0.1'
        TCP_PORT = 5005
        BUFFER_SIZE = 25000
       
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.bind((TCP_IP, TCP_PORT))
        self.sock.listen(1)

        while self.running:
            conn, addr = self.sock.accept()
            print 'DeviceRequestListener accepted a connexion request from: ', addr
            
            try:
                requestData = conn.recv(BUFFER_SIZE)
                print "DeviceRequestListener received a request..."
                requests.put_nowait(requestData)
                conn.send(requestData)  # echo
            except Exception, e:
                print e
                conn.close()
                self._close()


    def _close(self):
        self.sock.close()
        self.stop()

def waitForRequests():
    """
    Block while there is a tcp request to process.
    """
    while 1:
        try:
            request = requests.get(False) # Will block util an element can be extracted from the queue
            print "Request received in main thread..."
            handleRequest(request)
        except:
            pass

def handleRequest(requestData):
        """
        Expecting requestData like: '[1;2;3]'
        where 1 is target (controller)
              2 is method (function to call)
              3 is data (Optionnal)

        Example: [player;playTrack;{a content.Track object}]

        For now, only 'player' (see player.py) is availaible as a controller
        """
        print "Handling remote request..."
        
        args = requestData[1:-1].split(';')

        controllerName = args[0].strip()
        method = args[1].strip()   

        if controllerName == "player":
            controller = PLAYER
        else:
            controller = None

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
                method(castStrToDict(data))
            else:
                print "The method '{0}'' is not availaible on the specified controller.".format(method)
        else:
            print "Calling controller method without arguments..."
            getattr(controller, method)()


def castStrToDict(strValue):
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
            arrayOfDict.append(castStrToDict(arg))
        return arrayOfDict
    except:
        pass

def main(argv=None):
    if argv is None:
        argv = sys.argv

    #Listen for device requests
    server =  DeviceRequestListener()
    server.start()
    
    #Start a thread to handle incoming requests
    handleRequestThread = threading.Thread(target=waitForRequests)
    handleRequestThread.start()

    deviceMan = DeviceManager()
    #Local device is loaded by default
    thisDevice = deviceMan.getActiveDevice()

    #Start a thread to broadcast the server presence via UDP
    presenceBroadcaster = DevicePresenceBroadcaster(thisDevice)
    presenceBroadcaster.start()

    #Start the player main loop
    PLAYER.start()

    #Dispose ressources
    server.stop()
    handleRequestThread.stop()
    presenceBroadcaster.stop()


if __name__ == '__main__':
    sys.exit(main())



def testClient():
    import content as content
    tracks = content.getTracks()

    time.sleep(3) 
    request = "[player;playTrack;{0}]".format(str(tracks[5]))
    self.sendRequest(request)

    time.sleep(3) 
    request = "[player;queueTrack;{0}]".format(str(tracks[10]))
    self.sendRequest(request)

    time.sleep(3) 
    request = "[player;playNextTrack]"
    self.sendRequest(request)

    time.sleep(1) 
    request = "[player;queueTrack;{0}]".format(str(tracks[20]))
    self.sendRequest(request)


def testLocal():
    startServer()
    t1 = threading.Thread(target=waitForRequests)
    t1.start()
    PLAYER.start()




    




