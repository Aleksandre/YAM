
"""
This module holds Devices related components.
A 'Device' is any computer running the clientapp or the serverapp
"""

import logging
from ConfigParser import SafeConfigParser
import config as config
import time
from player import LocalPlayer, RemotePlayer
from socket import *
import select
import os
import threading

class DeviceManager:
    """
    Keeps a registry of known devices.    
    """
    def __init__(self, startWatcher = False, watcher = None):
        self.parser = SafeConfigParser()
        self.devicesRegistryPath = config.getConfigFolder() + "devices.ini"
        self.activeDevice = None
        self.bindEvents(startWatcher, watcher)

        #TODO : Load hostname and port from config
        self.deleteRegistry()
        self.registerLocalDevice()

    def registerLocalDevice(self):
        self.registerDevice(Device("local","My player", "localhost"))

    def bindEvents(self, startWatcher, watcher = None):
        self.deviceWatcher = None
        if startWatcher:
            if watcher:
                self.deviceWatcher = watcher
            else:
                self.deviceWatcher = DeviceWatcher(callback=self.handleDeviceNotificationReceived)
            self.deviceWatcher.start()

    def handleDeviceNotificationReceived(self, device):
        """
        TODO : Move this.
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
        If the registry could not be read, return None
        If no devices were found in the registry, return an empty array
        otherwise return an array of Devices.
        """
        filesRead = self.parser.read(self.devicesRegistryPath)
        if len(filesRead) == 0:
            print "The DeviceManager is creating the registry..."
            if not self.createRegistry():
                print "The DeviceManager could not create the registry."
                return None
        
        devices = []
        for device in self.parser.sections():
            url = self.parser.get(device, 'url').encode("utf-8")
            lastSeen = self.parser.get(device, 'lastSeen')
            visibleName = self.parser.get(device, 'visibleName').encode("utf-8")
            type = self.parser.get(device, 'type').encode("utf-8")
            device = Device(type, visibleName, url, lastSeen)
            devices.append(device)
        return devices

    def getLikelyActiveDevices(self):
        return self.getDevices()

    def registerDevice(self, device):
        """
        Register or update the specified device. Devices are stored into the file devices.ini
        from the config folder.
        """
        if not isinstance(device, Device):
            error = "The specified device argument must inherit from the type devices.Device."
            logging.info(error)
            raise TypeError(error)


        filesRead = self.parser.read(self.devicesRegistryPath)
        if len(filesRead) == 0:
            print "The DeviceManager is creating the registry..."
            if not self.createRegistry():
                print "The DeviceManager could not create the registry."
                return False

        currentDevices = self.getDevices()
        if not currentDevices == None and device in currentDevices:
            self.updateDeviceLastSeenTime(device)
            return True

        sectionName = device.visibleName
        self.parser.add_section(sectionName)
        self.parser.set(sectionName, 'visibleName', device.visibleName)
        self.parser.set(sectionName, 'url', device.url)
        self.parser.set(sectionName, 'type', device.type)
        self.parser.set(sectionName, 'lastSeen', str(device.lastSeen))
        with open(self.devicesRegistryPath,'w') as f:
            self.parser.write(f)
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

       # if activeDevice.type == "local":
         #   return LocalPlayer(self.mainApp)
        #elif activeDevice.type == "remote":
         #   return RemotePlayer(activeDevice.url)

    def getActiveDevice(self):
        if self.activeDevice == None:
            devices = self.getDevices()
            for device in devices:
                if device.type == "local":
                    print "No device were selected. Using local device '{0}' as default.".format(device.visibleName)
                    self.activeDevice = device
                    break
        return self.activeDevice

    def getActiveDeviceType(self):
        activeDev = self.getActiveDevice()
        if activeDev:
            return activeDev.type
        else :
            return None

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
            with open(self.devicesRegistryPath,'w') as f:
                self.parser.write(f)
            
            #print "Updated device lastSeen time: {0}".format(lastSeen)

    def createRegistry(self):
        try:
            with open(self.devicesRegistryPath, 'w+') as f:
                print f
                return True
        except Exception as e:
            print e
            return False

    def isWatching(self):
        if self.deviceWatcher:
            return self.deviceWatcher.isRunning()
        else:
            return False

  
    def deleteRegistry(self):
        try:
            self.parser = SafeConfigParser()
            with open(self.devicesRegistryPath,'w') as f:
                self.parser.write(f)
            return True
        except Exception as e:
            print e
            return False

    def dispose(self):
        print "Disposing DeviceManager..."
        if self.deviceWatcher:
            self.deviceWatcher.stop()

class DeviceWatcher():
    """
    Watch for other devices presence broadcasts.
    """
    def __init__(self, portToWatch = 5555, callback = None):
        self.portToWatch = portToWatch or config.getProperty("presence_watcher_watched_port")
        self.running = False
        self.bufferSize = 1024
        self.callback = callback
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.bind(('', self.portToWatch))
        self.thread = threading.Thread(target=self._run, name="watcher")

    def start(self):
        print "Starting to watch for devices UDP broadcasts on port: {0}...".format(self.portToWatch)
        self.running = True
        self.thread.start()

    def isRunning(self):
        return self.running 

    def stop(self):
        print "Stopping DeviceWatcher..."
        self.running = False
        self.sock.close()
        print "Stopped DeviceWatcher."

    def _run(self):
        print "Started DeviceWatcher."
        try:
            while self.running:
                data, addr = self.sock.recvfrom(self.bufferSize)
                print "Broadcast received from : {0}".format(addr)
                print data
                if self.callback:
                    decodedMsg = Device.fromEncodedString(data)
                    #Do no call back for invalid messages
                    if decodedMsg:
                        self.callback(decodedMsg)
        finally:
            self.sock.close()

    def getProcName(self):
        return self.thread.name

class DevicePresenceBroadcaster():
    """
    Notify other devices the presence of this device.
    """
    def __init__(self, thisDevice, portToTarget = 5555, delayBetweenBroadcastsInSec = 5):
        self.port = portToTarget or config.getProperty("presence_broadcaster_target_port")
        self.delay = delayBetweenBroadcastsInSec or config.getProperty("presence_broadcaster_call_delay_seconds")
        self.thisDevice = thisDevice
        self.running = False
       
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind(('', 0))
        self.sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.thread = threading.Thread(target=self._run, name="broadcaster")

    def start(self):
        print "Starting PresenceBroadcaster with delay =", self.delay, "seconds"
        self.running = True
        self.thread.start()

    def isRunning(self):
        return self.running

    def stop(self):
        print "Stopping DevicePresenceBroadcaster..."
        self.running = False
        self.sock.close()
        print "Stopped PresenceBroadcaster."

    def _run(self):
        print "Started PresenceBroadcaster."
        try:
            while self.running:
                try:
                    data = self.thisDevice.encodeForTransport() 
                    self.sock.sendto(data, ('<broadcast>', int(self.port)))
                    print "Broadcasting {0} presence on UDP port: {1}".format(self.thisDevice.visibleName, self.thisDevice.port)
                except Exception as e:
                    print e
                    #Wait if broadcaster is running
                if self.running:
                    time.sleep(self.delay)
        finally:
            self.stop()

    def getProcName(self):
        return self.thread.name


class Device:
    """
    A 'Device' is any computer running the clientapp or the serverapp
    """
    def __init__(self, type="local", visibleName = None, url = None, lastSeen = None):
        print "Instanciating device with url: {0}".format(url)
        self.visibleName = visibleName
        self.url = url or "0:0"
        self.lastSeen = lastSeen or time.localtime()
        self.type = type
        if ':' in url:
            self.host, self.port = url.split(':')
        else:
            self.host = url

    def isLikelyActive(self):
        lastSeenTime = time.fromtimestamp(self.lastSeen)
        print time.localtime() - lastSeenTime
        return self.lastSeen 

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
        return "{0};{1}".format(self.visibleName, self.url)

    @staticmethod
    def decode(encodedString):
        args =  encodedString.split(';')
        name = args[0]
        url = args[1]
        #print "Decoded device string: {0}, {1}: ".format(name, url)
        return name, url

def testPresenceBroadcaster():
    thisDevice = Device(url="localhost:5000", visibleName="test-device")
    bc = DevicePresenceBroadcaster(thisDevice, delayBetweenBroadcastsInSec=1)
    watcher = DeviceWatcher()
    watcher.start()
    bc.start()
    time.sleep(5)
    bc.stop()
    watcher.stop()

if __name__ == '__main__':
    config.setConfigFolder('../config/')
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

