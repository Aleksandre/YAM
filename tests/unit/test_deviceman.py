import sys
sys.path.append("yam")

import pytest
from devices import DeviceManager, Device, DevicePresenceBroadcaster, DeviceWatcher
import config
import time
import psutil
import os

class TestDeviceMan:

    config.setConfigFolder('tests/config/')
    deviceMan = DeviceManager()
    deviceMan.deleteRegistry()
    receivedBroadcast = False
    device = Device(type="remote", visibleName="testDevice", url="testLocation", lastSeen=time.localtime())

    def test_registry_not_found(self):
        self.deviceMan.deleteRegistry()
        assert self.deviceMan.createRegistry() == True
        assert self.deviceMan.getDevices() == []
        assert self.deviceMan.deleteRegistry()

    def test_delete_registry(self):
        self.deviceMan.deleteRegistry()
        assert self.deviceMan.createRegistry()
        assert os.path.isfile(self.deviceMan.devicesRegistryPath)
        self.deviceMan.deleteRegistry()
        assert len(self.deviceMan.getDevices()) == 0
        
    def test_add_entry_to_registry(self):
        self.deviceMan.deleteRegistry()
        self.deviceMan.registerDevice(self.device)
        assert self.device in self.deviceMan.getDevices()
        assert len(self.deviceMan.getDevices()) == 1
        savedDevice = self.deviceMan.getDevices()[0]
        assert savedDevice.type == self.device.type
        assert savedDevice.visibleName == self.device.visibleName
        assert savedDevice.url == self.device.url
        #assert savedDevice.lastSeen == self.device.lastSeen

    def test_device_watcher_can_start_and_stop(self):
        self.deviceManWithBc = DeviceManager(startWatcher=True)
        assert self.deviceManWithBc.isWatching() == True
        self.deviceManWithBc.dispose()
        assert self.deviceManWithBc.isWatching() == False

    def test_device_watcher_can_receive(self):
        self.watcher = DeviceWatcher(portToWatch=5555, callback=self.assert_watcher_receive_correct_data)
        self.watcher.start()
        assert self.watcher.isRunning() == True
        
        self.remoteDevice = Device(type="remote", visibleName="remoteDevice", url="localhost:5021", lastSeen=time.localtime())
        presenceBroadcaster = DevicePresenceBroadcaster(self.remoteDevice, delayBetweenBroadcastsInSec=1)
        self.receivedBroadcast == False
        presenceBroadcaster.start()
        assert presenceBroadcaster.isRunning()
        time.sleep(1)
        assert self.receivedBroadcast == True
        presenceBroadcaster.stop()
        assert presenceBroadcaster.isRunning() == False
        self.watcher.stop()
        assert self.watcher.isRunning() == False

    def assert_watcher_receive_correct_data(self, device):
        assert device == self.remoteDevice
        self.receivedBroadcast = True

    def test_deviceman_and_watcher_integration(self):
        self.watcher = DeviceWatcher(portToWatch=5555, callback=self.assert_watcher_receive_correct_data)
        self.deviceManWithBc = DeviceManager(startWatcher=True, watcher=self.watcher)

        assert self.deviceManWithBc.isWatching() == True
        
        self.remoteDevice = Device(type="remote", visibleName="remoteDevice", url="localhost:5021", lastSeen=time.localtime())
        presenceBroadcaster = DevicePresenceBroadcaster(self.remoteDevice, delayBetweenBroadcastsInSec=1)
        self.receivedBroadcast == False
        presenceBroadcaster.start()
        assert presenceBroadcaster.isRunning()
        time.sleep(1)
        assert self.receivedBroadcast == True
        presenceBroadcaster.stop()
        assert presenceBroadcaster.isRunning() == False
        self.deviceManWithBc.dispose()
        assert self.watcher.isRunning() == False

    def test_deviceman_default_watcher(self):
        self.deviceManWithBc = DeviceManager(startWatcher=True)
        assert self.deviceManWithBc.isWatching() == True
        
        self.remoteDevice = Device(type="remote", visibleName="remoteDevice", url="localhost:5021", lastSeen=time.localtime())
        presenceBroadcaster = DevicePresenceBroadcaster(self.remoteDevice, delayBetweenBroadcastsInSec=1)
        presenceBroadcaster.start()
        assert presenceBroadcaster.isRunning()
        time.sleep(1)
        presenceBroadcaster.stop()
        assert presenceBroadcaster.isRunning() == False
        self.deviceManWithBc.dispose()
        assert self.deviceManWithBc.isWatching() == False

    def test_set_active_device(self):
        self.deviceMan.setActiveDevice(self.device)
        assert self.deviceMan.getActiveDevice() == self.device

    def test_clear_registry(self):
        pass

    def test_watcher_does_not_leak(self):
        try:
            self.watcher = DeviceWatcher(portToWatch=5555, callback=self.assert_watcher_receive_correct_data)
            self.watcher.start()
            assert self.watcher.isRunning() == True
            self.watcher.stop()
            procName = self.watcher.getProcName()

            isReallyRunning = False
            for proc in psutil.process_iter():
                if proc.name == self.watcher.getProcName():
                    assert proc.status == psutil.STATUS_RUNNING
                    isReallyRunning == True
            assert isReallyRunning
            self.watcher.stop()
            assert self.watcher.isRunning() == False
            
            isReallyClosed = True
            for proc in psutil.process_iter():
                if proc.name == procName:
                    isReallyClosed = False
            assert isReallyClosed

        except Exception as e:
            print e
            #May not work on all platform
            #TODO : Make it work on MAC
            self.watcher.stop()
            pass

    def test_concurrent_watchers(self):
        self.watcher1 = DeviceWatcher(portToWatch=5555, callback=self.assert_watcher_receive_correct_data)
        self.watcher1.start()
        assert self.watcher1.isRunning() == True

        self.watcher2 = DeviceWatcher(portToWatch=5555, callback=self.assert_watcher_receive_correct_data)
        self.watcher2.start()
        assert self.watcher2.isRunning() == True

        presenceBroadcaster = DevicePresenceBroadcaster(self.device, delayBetweenBroadcastsInSec=1)
        presenceBroadcaster.start()

        time.sleep(1)

        self.watcher1.stop()
        self.watcher2.stop()
        presenceBroadcaster.stop()

