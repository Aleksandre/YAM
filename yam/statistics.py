

import config
from datetime import datetime

def addPlayedTrack(track):
	"""
	Adds an entry to the play history
	"""
	assert track != None
	fileName = config.getFullFileName('play_history.txt')
	entry = "{0} {1}".format(datetime.now(), track.filePath)
	try:
		with open(fileName, 'a') as f:
			f.write(entry + "\n")
			return True
	except IOError as e:
		print e
		return False