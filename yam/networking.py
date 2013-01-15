from socket import *
import threading
from player import LocalPlayer
import Queue
from content import Mock
import time
import socket
from devices import DeviceManager, DevicePresenceBroadcaster
import select

PLAYER = LocalPlayer()
PLAYER.setHeadless()
requests = Queue.Queue()

class DeviceOrderListener:
    def __init__(self):
        self.running = True
        self.thread = threading.Thread(target=self._run)

    def start(self):
        self.thread.start()

    def stop(self):
        print "Stopping TCP listener"
        self.running = False

    def _run(self):
        TCP_IP = '127.0.0.1'
        TCP_PORT = 5005
        BUFFER_SIZE = 25000
       
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((TCP_IP, TCP_PORT))
        s.listen(1)

        while self.running:
            conn, addr = s.accept()
            print 'TCP listener accepted a connexion request from: ', addr
            
            try:
                requestData = conn.recv(BUFFER_SIZE)
                print "TCP listener received a request..."
                requests.put_nowait(requestData)
                conn.send(requestData)  # echo
            except Exception, e:
                print e
                s.close()
                conn.close()
                self.stop()



class TestClient:
    def __init__(self):
        self.thread = threading.Thread(target=self._run)
        self.tcpIP = '127.0.0.1'
        self.tcpPort = 5005
        self.bufferSize = 1024

    def start(self):
        self.thread.start()

    def _run(self):
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
        
    def sendRequest(self, request):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.tcpIP, self.tcpPort))

        s.send(request)
        data = s.recv(self.bufferSize)
        print "Server answered the client request...", data
        s.close()


class RemoteClient:
    def __init__(self):
        self.tcpIP = '192.168.1.127'
        self.tcpPort = 5005
        self.bufferSize = 1024

    def sendRequest(self, request):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.tcpIP, self.tcpPort))

        s.send(request)
        data = s.recv(self.bufferSize)
        print "Server answered the client request...", data
        s.close()



def waitForRequests():
    while True:
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
        """
        print "Handling remote request..."
        
        args = requestData[1:-1].split(';')

        controllerName = args[0].strip()
        method = args[1].strip()    
        controller = getControllerByName(controllerName)

        #Call controller method
        if len(args) >= 3:
            data = args[2].strip()
            method = getattr(controller, method)
            if method:
                method(castStrToDict(data))
            else:
                pass
        else:
            print "Calling method without arguments..."
            print getattr(controller, method)()


def getControllerByName(controllerName):
    if controllerName == "player":
        return PLAYER  

def castStrToDict(strValue):
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

def startClient():
    client = TestClient()
    client.start()

    


def testLocal():
    startServer()
    t1 = threading.Thread(target=waitForRequests)
    t1.start()
    PLAYER.start()

def testRemote():
    #startServer()
    #t1 = threading.Thread(target=waitForRequests)
    #t1.start()
    startClient()

def main():
    server = DeviceOrderListener()
    server.start()
    
    t1 = threading.Thread(target=waitForRequests)
    t1.start()

    deviceMan = DeviceManager()
    thisDevice = deviceMan.getActiveDevice()
    presenceBroadcaster = DevicePresenceBroadcaster(thisDevice)
    presenceBroadcaster.start()

    PLAYER.start()


if __name__ == '__main__':
   main()




    




