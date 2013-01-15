import logging
from ConfigParser import SafeConfigParser
import config
import time
from player import LocalPlayer, RemotePlayer

class DeviceManager:

    def __init__(self, mainApp):
        self.parser = SafeConfigParser()
        self.devicesRegistryPath = config.getConfigFolder() + "devices.ini"
        self.activeDevice = None
        self.mainApp = mainApp

    def handleDeviceNotificationReceived(self, deviceName, url):
        """
        This method is triggered each time another device
        on the network broadcasted it's presence.

        If the device is already present in the devices registry,
        updates the device-last-seen field in the registry.

        If the device is not yet in the registry,
        add it and set device-last-seen to now.
        """
        device = Device("remote", deviceName, url)
        self.registerDevice(device)

    def getDevices(self):
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

class Device:
    def __init__(self, type="local", visibleName = None, url = None, lastSeen = None):
        self.visibleName = visibleName
        self.url = url
        self.lastSeen = lastSeen or time.localtime()
        self.type = type

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.visibleName == other.visibleName)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.visibleName  + " [{0}]".format(self.type)

    def __str__(self):
        return self.visibleName, self.url

if __name__ == '__main__':
    man = DeviceManager()
    man.handleDeviceNotificationReceived("rpi-yam","192.168.1.127:5005")
    print man.printRegisteredDevices()
