import sys
sys.path.append("yam")
sys.path.append("../../yam")

from serverapp import YamTcpServer
from devices import DeviceWatcher
from player import RemoteClient
import config as config
import serverapp
import time
import SocketServer
import threading

request_received = False
answer = None
tcpServer = None
tcpServerReallyBroadcastedItsPresence = False

class TestServerApp:

	config.setConfigFolder('tests/config/')
	request_received_confirmed = False

	def test_server_default_setup(self):
		pass
		server = serverapp.setupTestServer()
		global tcpServer 
		tcpServer = server
		
		t = threading.Thread(target=self.send_requests_and_quit, name="reqsender")
		t.start()
		
		watcher = DeviceWatcher(callback=self.device_watcher_callback)
		watcher.start()

		tcpServer.start()
		watcher.stop()
		global tcpServerReallyBroadcastedItsPresence
		assert tcpServerReallyBroadcastedItsPresence
		
	def send_requests_and_quit(self):
		time.sleep(1)
		global tcpServer
		ip, port = tcpServer.tcpServer.server_address
		self.requestSender = RemoteClient("{0}:{1}".format(ip, port),callback=self.on_request_callback)
		self.request = "player;getState\n"
		self.requestSender.sendRequest(self.request)
		return

	def on_request_callback(self, answer):
		global tcpServer
		assert answer and len(answer) > 0 and answer == "STOPPED"
		tcpServer.stop()

	def device_watcher_callback(self, device):
		global tcpServerReallyBroadcastedItsPresence
		tcpServerReallyBroadcastedItsPresence = True

		global tcpServer
		assert tcpServer.device == device


