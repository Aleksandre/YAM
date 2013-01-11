import logging
from ConfigParser import SafeConfigParser

class DevicesManager:
    def __init__(self):
        self.parser = SafeConfigParser()
        self.configFileName = '../config/devices.ini'
        self.reloadDevices()

    def reloadDevices(self):
        filesRead = self.parser.read(self.configFileName)

        if len(filesRead) == 0:
            error = "The DeviceManager could not load it's configuration file: " + self.configFileName
            logging.error(error)
            raise Exception(error)
        else:
            self.registeredDevices = []
            for device in self.parser.sections():
                deviceUri = self.parser.get(device, 'uri')
                device = Device(device, deviceUri)
                self.registeredDevices.append(device)

    def registerDevice(self, device):
        if not isinstance(device, Device):
            error = "The specified device argument must inherit from the type Device."
            logging.info(error)
            raise TypeError(error)

        if device in self.registeredDevices:
            msg = "The device is already registered: ", device.visibleName, device.url
            print msg
            logging.info(msg)
            return False

        filesRead = self.parser.read(self.configFileName)
        if len(filesRead) == 0:
            error = "The DeviceManager could not load it's configuration file: " + self.configFileName
            logging.error(error)
            raise Exception(error)
        else:
            self.parser.add_section(device.visibleName)
            self.parser.set(device.visibleName, 'uri', device.url)
            self.parser.write(file(self.configFileName,'w'))
            self.reloadDevices()
            return True

    def printRegisteredDevices(self):
        for device in self.registeredDevices:
            print device.visibleName

    def getDevices(self):
        return self.registeredDevices



class Device:
    def __init__(self, visibleName = None, url = None):
        self.visibleName = visibleName
        self.url = url

    def isResponding(self):
        return True

    def tryRegister(self):
        return True

    def isRegistered(self):
        return False

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.visibleName, self.url

    def __str__(self):
        return self.visibleName

if __name__ == '__main__':
    man = DevicesManager()
    man.registerDevice(Device("Mine","woot"))
