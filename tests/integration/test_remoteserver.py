import sys
sys.path.append("yam")
sys.path.append("../../yam")

from player import RemoteClient, RemotePlayer
import time
import content as content

class TestRemoteServer():

	assert_server_really_answ = False

	def test_can_send_cmd(self):
		host_address = "127.0.0.1:5005"
		remoteClient = RemoteClient(host_address, callback=self.assert_server_answered)
		remoteClient.sendRequest('player;getState')
		time.sleep(3)
		assert self.assert_server_really_answ

	def assert_server_answered(self, answer):
		print answer
		assert answer == "STOPPED"
		global assert_server_really_answ
		assert_server_really_answ = True

