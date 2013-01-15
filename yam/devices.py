import logging
from ConfigParser import SafeConfigParser
import config
import time
from player import LocalPlayer, RemotePlayer
from socket import *
import select
import threading


class DeviceManager:
    """
    Holds device related logic.
    A device is an application running any version of YAM.
    """
    def __init__(self, mainApp = None):
        self.parser = SafeConfigParser()
        self.devicesRegistryPath = config.getConfigFolder() + "devices.ini"
        self.activeDevice = None
        self.mainApp = mainApp
        self.bindEvents()

    def bindEvents(self):
        self.deviceWatcher = DeviceWatcher(callback=self.handleDeviceNotificationReceived)
        self.deviceWatcher.start()
        pass

    def handleDeviceNotificationReceived(self, device):
        """
        This method is triggered each time another device
        on the network broadcasted it's presence.

        If the device is already present in the devices registry,
        updates the device-last-seen field in the registry.

        If the device is not yet in the registry,
        add it and set device-last-seen to now.
        """
        self.registerDevice(device)

    def getDevices(self):
        """
        Read all configured devices from the registry.
        """
        filesRead = self.parser.read(self.devicesRegistryPath)

        if len(filesRead) == 0:
            error = "The DeviceManager could not load it's configuration file: {0}".format(self.devicesRegistryPath)
            logging.error(error)
            raise Exception(error)
        else:
            devices = []
            for device in self.parser.sections():
                url = self.parser.get(device, 'url').encode("utf-8")
                lastSeen = self.parser.get(device, 'lastSeen')
                visibleName = self.parser.get(device, 'visibleName').encode("utf-8")
                type = self.parser.get(device, 'type').encode("utf-8")
                device = Device(type, visibleName, url, lastSeen)
                devices.append(device)
            return devices

    def registerDevice(self, device):
        """
        Register or update the specified device. Devices are stored into the file devices.ini
        from the config folder.
        """
        if not isinstance(device, Device):
            error = "The specified device argument must inherit from the type devices.Device."
            logging.info(error)
            raise TypeError(error)

        currentDevices = self.getDevices()
        if device in currentDevices:
            self.updateDeviceLastSeenTime(device)
            return True

        filesRead = self.parser.read(self.devicesRegistryPath)
        if len(filesRead) == 0:
            error = "The DeviceManager could not load it's configuration file: {0}".format(self.devicesRegistryPath)
            logging.error(error)
            raise Exception(error)
        else:
            sectionName = device.visibleName
            self.parser.add_section(sectionName)
            self.parser.set(sectionName, 'visibleName', device.visibleName)
            self.parser.set(sectionName, 'url', device.url)
            self.parser.set(sectionName, 'type', device.type)
            self.parser.set(sectionName, 'lastSeen', str(device.lastSeen))
            self.parser.write(file(self.devicesRegistryPath,'w'))
            print "Added device to the registry: {0} {1}".format(device.visibleName, device.url)
            return True

    def printRegisteredDevices(self):
        for device in self.getDevices():
            print device.visibleName

    def getActivePlayer(self):
        activeDevice = self.getActiveDevice()
        if activeDevice == None:
            print "There is no active player to select."
            return

        if activeDevice.type == "local":
            return LocalPlayer(self.mainApp)
        elif activeDevice.type == "remote":
            return RemotePlayer(activeDevice.url)

    def getActiveDevice(self):
        if self.activeDevice == None:
            devices = self.getDevices()
            for device in devices:
                if device.type == "local":
                    print "No device were selected. Using local device '{0}' as default.".format(device.visibleName)
                    self.activeDevice = device
                    break
        return self.activeDevice

    def setActiveDevice(self, device):
        print "Set '{0}' as active device.".format(device.visibleName)
        self.activeDevice = device

    def updateDeviceLastSeenTime(self, device):
        filesRead = self.parser.read(self.devicesRegistryPath)

        if len(filesRead) == 0:
            error = "The DeviceManager could not load it's configuration file: {0}".format(self.devicesRegistryPath)
            logging.error(error)
            raise Exception(error)
        else:
            sectionName = device.visibleName
            lastSeen = device.lastSeen
            self.parser.set(sectionName, 'lastSeen', str(lastSeen))
            self.parser.write(file(self.devicesRegistryPath,'w'))
            print "Updated device lastSeen time: {0}".format(lastSeen)


    def clearRegistry(self):
        filesRead = self.parser.read(self.devicesRegistryPath)
        if len(filesRead) == 0:
            error = "The DeviceManager could not load it's configuration file: {0}".format(self.devicesRegistryPath)
            logging.error(error)
            raise Exception(error)
        else:
            pass
            #TODO


class DeviceWatcher():
    """
    Watch for other devices presence broadcasts.
    """
    def __init__(self, portToWatch = 5555, callback = None):
        self.portToWatch = portToWatch or config.getProperty("presence_watcher_watched_port")
        self.running = False
        self.bufferSize = 1024
        self.callback = callback

    def start(self):
        print "Starting PresenceWatcher on UDP port: {0}...".format(self.portToWatch)
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def stop(self):
        print "Stopping PresenceWatcher..."
        self.running = False

    def _run(self):
        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(('<broadcast>', self.portToWatch))
        s.setblocking(0)
        print "Started PresenceWatcher."
        while self.running:
            result = select.select([s],[],[])
            msg = result[0][0].recv(self.bufferSize) 
            print "Received UDP broadcast msg: {0}".format(msg)
            if self.callback:
                self.callback(Device.fromEncodedString(msg))
        print "Stopped PresenceWatcher."



class DevicePresenceBroadcaster():
    """
    Notify other devices the presence of this device.
    """
    def __init__(self, thisDevice, portToTarget = 5555, delayBetweenBroadcastsInSec = 5):
        self.port = portToTarget or config.getProperty("presence_broadcaster_target_port")
        self.delay = delayBetweenBroadcastsInSec or config.getProperty("presence_broadcaster_call_delay_seconds")
        self.thisDevice = thisDevice
        self.running = False

    def start(self):
        print "Starting PresenceBroadcaster with delay =", self.delay, "seconds"
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def stop(self):
        print "Stopping PresenceBroadcaster..."
        self.running = False

    def _run(self):
        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(('', 0))
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        
        print "Started PresenceBroadcaster."
        while self.running:
            data = self.thisDevice.encodeForTransport() 
            s.sendto(data, ('<broadcast>', int(self.port)))
            print "Broadcasting {0} presence on UDP port: {1}".format(self.thisDevice.visibleName, self.port)
            time.sleep(self.delay)
        print "Stopped PresenceBroadcaster."

class Device:
    """

    """
    def __init__(self, type="local", visibleName = None, url = None, lastSeen = None):
        self.visibleName = visibleName
        self.url = url
        self.lastSeen = lastSeen or time.localtime()
        self.type = type

    @staticmethod
    def fromEncodedString(encodedString):
        """
        Copy constructor for Device object encoded wit hencodeForTransport
        """
        visibleName, url = Device.decode(encodedString) 
        return Device("remote", visibleName=visibleName, url=url)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.visibleName == other.visibleName)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.visibleName  + " [{0}]".format(self.type)

    def __str__(self):
        return self.visibleName, self.url


    def encodeForTransport(self):
        return "[{0};{1}]".format(self.visibleName, self.url) + '\n'

    @staticmethod
    def decode(encodedString):
        args =  encodedString[1:-1].split(';')
        name = args[0]
        url = args[1]
        return name, url


def testPresenceBroadcaster():
    thisDevice = DeviceManager().getActiveDevice()
    bc = DevicePresenceBroadcaster(thisDevice)
    #watcher = DeviceWatcher()
    #watcher.start()
    bc.start()
    time.sleep(5)
    bc.stop()
    #watcher.stop()

if __name__ == '__main__':
    testPresenceBroadcaster()
    #man = DeviceManager()
   # man.handleDeviceNotificationReceived("rpi-yam","192.168.1.127:5005")
    #print man.printRegisteredDevices()

def startPresenceBroadcaster():
    from devices import Device
    thisDevice = Device("rpi")
    PRESENCE_BROADCASTER = DevicePresenceBroadcaster(thisDevice)
    PRESENCE_BROADCASTER.start()

def stopPresenceBroadcaster():
    if PRESENCE_BROADCASTER:
        PRESENCE_BROADCASTER.stop()

