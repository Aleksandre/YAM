import sys
sys.path.append("yam")
sys.path.append("../../yam")

import config, clientapp, threading
import time
from devices import DevicePresenceBroadcaster, Device
from player import LocalPlayer, RemotePlayer

class TestClientApp:

	config.setConfigFolder('tests/config/')
	clientReceivedBroadcastMsg = False
	device = Device(type="remote",visibleName="test-device")
	app = None

	def test_app_can_watch_devices(self):
		global app
		app = clientapp.setupTestClient()
		app.deviceMan.deleteRegistry()
		t = threading.Thread(target=self.send_presence_broadcast_to_device)
		t.start()
		app.start()
		time.sleep(2)
		assert self.device in app.deviceMan.getDevices()
		app.deviceMan.deleteRegistry()

	def send_presence_broadcast_to_device(self):
		broadcaster = DevicePresenceBroadcaster(self.device, delayBetweenBroadcastsInSec=1)
		broadcaster.start()
		time.sleep(5)
		broadcaster.stop()
		global app
		app.stop()

	def test_app_can_select_device(self):
		global app
		app.deviceMan.deleteRegistry()
		app.deviceMan.registerLocalDevice()

		app.updatePlayer()	
		assert isinstance(app.player , LocalPlayer)

		app.deviceMan.deleteRegistry()

		device = Device(type="remote",visibleName="test-client-app", url="localhost:0")
		app.deviceMan.registerDevice(device)
		app.deviceMan.setActiveDevice(device)

		app.updatePlayer()
		assert isinstance(app.player, RemotePlayer)

		app.stop()
		app.deviceMan.deleteRegistry()

	def test_app_can_send_request_to_remote_device(self):
		global app


	def test_app_does_not_leak(self):
		pass


