
"""
This module holds differents implementation of Player like : local, remote and stream (coming soon)
"""
import sys
import os
from PySide import QtCore, QtGui
from PySide.QtCore import *
from PySide.QtGui import *
from networking import RemoteClient
from content import Mock, Track
try:
    from PySide.phonon import Phonon
except ImportError as error:
    print error
    sys.exit(1)

def getPlayerByType(device):
    if device.type == "local":
        return LocalPlayer(prefinishMark=0)
    if device.type == "remote":
        return RemotePlayer(device.host, device.port)

class PlayerStates:
    STOPPED="STOPPED"
    PLAYING="PLAYING"
    PAUSED="PAUSED"
    ERROR = "ERROR"

class LocalPlayer(QtCore.QObject):
    """
    The LocalPlayer uses the QtPhonon module to play music files
    """
    #Emit a signal whenever the player state changes
    stateChanged = QtCore.Signal(str)

    #Emit a signal whenever the player source changes
    sourceChanged = QtCore.Signal(Track)

    #Emit time elapsed in ms since the current source started playing 
    ticked = QtCore.Signal(int)

    #Holds a list of hosts interested by the player state
    hostsInterestedByState = []

    _playlist = []
    _playlistIdx = 0

    def __init__(self, loadForClient = False, prefinishMark=5000, log_played_tracks=True): 
        QtCore.QObject.__init__(self)
        try:
            self.app = QtGui.QApplication(sys.argv)
        except RuntimeError:
            """
            Only one QApplication can be active.
            """
            self.app = QtCore.QCoreApplication.instance()
        self.app.aboutToQuit.connect(self.exit)
        self.log_played_tracks = log_played_tracks
        self.init(prefinishMark)

    def init(self, prefinishMark):
        self.audioOutput = Phonon.AudioOutput(Phonon.MusicCategory, self.app)
        self.player = Phonon.MediaObject(self.app)
        self.player.setPrefinishMark(prefinishMark)
        self.player.setTickInterval(1000)
        Phonon.createPath(self.player, self.audioOutput)
        self._bindEvents()

    def registerToStateChanges(self, target):
        print target
        #print "Registering host for state change {0}".format(target)
        if not target in self.hostsInterestedByState:
            self.hostsInterestedByState.append(target)
            return True
        return False

    def unregisterToStateChanges(self, target):
        if target in self.hostsInterestedByState:
            self.hostsInterestedByState.remove(target)
            return True
        return False

    def setHeadless(self):
        self.app.setApplicationName('headless-player')

    def seek(self, timeInMs):
        print "Seeking track at: {0}".format(timeInMs)
        self.player.seek(long(timeInMs))

    def currentPlaylist(self):
        return self._playlist 
    
    def hasNextTrack(self):
        return self._playlistIdx + 1 < len(self._playlist) 
    
    def hasPreviousTrack(self):
        return  self._playlistIdx > 0

    def currentlyPlayingTrack(self):
        return self._playlist[self._playlistIdx]

    def playTrack(self, track):
        self._resetPlaylist()

        trackPath = os.path.realpath(track.filePath)
        print "Playing track: ", track.title
        
        self.player.setCurrentSource(Phonon.MediaSource(trackPath))
        self._playlist.append(track)
        self.player.play()
        return self.getState() == "PLAYING"

    def playTracks(self, tracks=[]):
        self._resetPlaylist()
        for track in tracks:
            self.queueTrack(track, emit=False)

        firstTrack = Phonon.MediaSource(self._playlist[self._playlistIdx].filePath)
        self.player.setCurrentSource(firstTrack)
        self.player.play()
        return self.getState() == "PLAYING"

    def playNextTrack(self):
        print "Playing next track..."
        if self.hasNextTrack():
            self._playlistIdx = self._playlistIdx + 1
            nextTrack = Phonon.MediaSource(self._playlist[self._playlistIdx].filePath)
            print nextTrack
            print self.player.setCurrentSource(nextTrack)
            print self.player.play()
        return self.getState() == "PLAYING"

    def playPreviousTrack(self):
        if self.hasPreviousTrack():
            self._playlistIdx = self._playlistIdx - 1
            previousTrack = Phonon.MediaSource(self._playlist[self._playlistIdx].filePath)
            self.player.setCurrentSource(previousTrack)
            self.player.play()
        return self.getState() == "PLAYING"

    def queueTrack(self, track, emit=True):
        print "Queuing track: ", track
        self._playlist.append(track)
        self.stateChanged.emit(self.getState())
        return track in self._playlist

    def queueTracks(self, tracks):
        for track in tracks:
            self.queueTrack(track, emit=False)
        self.stateChanged.emit(self.getState())
        return True

    def stop(self):
        print "Stopping player"
        self.player.stop()
        return self.getState() == "STOPPED"

    def resume(self):
        self.player.play()
        return self.getState() == "PLAYING"

    def pause(self):
        self.player.pause()
        return self.getState() == "PAUSED"

    def getCurrentTime(self):
        self.player.currentTime()

    def getState(self):
        playerState = self.player.state()

        if playerState == Phonon.StoppedState:
            return PlayerStates.STOPPED
        if playerState == Phonon.PlayingState:
            return PlayerStates.PLAYING
        if playerState == Phonon.PausedState:
            return PlayerStates.PAUSED
        if playerState == Phonon.ErrorState:
            return PlayerStates.ERROR

        return "INVALID"

    def togglePlayState(self):
        """
        If the player is playing, it will be paused.
        If the player is paused, playback will be resumed.
        If the player is stopped, do nothing.
        """
        state = self.getState()
        if state == PlayerStates.PAUSED:
            self.resume()
        elif state == PlayerStates.PLAYING:
            self.pause()
        self.stateChanged.emit(self.getState())
        return True

    def notifyStateChanged(self):
        print "changed"

    def _stateChanged(self, state, state1):
        self.stateChanged.emit(self.getState())

    def _sourceChanged(self, source):
        self.sourceChanged.emit(self.getState())

    def _aboutToFinish(self):

        if self.log_played_tracks:
            import statistics
            statistics.addPlayedTrack(self._playlist[self._playlistIdx])

        print "Player is about to finish playing the current track..."
        if self.hasNextTrack():
            if self.getState() == "STOPPED":
                self.playNextTrack()
            else:
                self._playlistIdx = self._playlistIdx + 1
                nextTrack = Phonon.MediaSource(self._playlist[self._playlistIdx].filePath)
                self.player.enqueue(nextTrack)
        else:
            print "It was the last track, do nothing."

    def _bindEvents(self):
        #self.player.currentSourceChanged.connect(self._sourceChanged)
        self.connect(self.player, SIGNAL('tick(qint64)'), self._tick)
        self.connect(self.player, SIGNAL('stateChanged(Phonon::State, Phonon::State)'), self._stateChanged)
        self.connect(self.player, SIGNAL('aboutToFinish()'), self._aboutToFinish)


    def _tick(self, timeSinceBeginInMs):
        self.ticked.emit(timeSinceBeginInMs)
    
    def _resetPlaylist(self):
        self._playlist = []
        self._playlistIdx = 0
        self.player.clearQueue()

    def start(self):
        """
        This is a blocking call.
        When the player is used without an interface,
        it must run it's own app event loop to enable QtEvents and QtSignals.
        """
        self.app.exec_()

    def exit(self):
        """
        When the player is used without an interface,
        this stops the app event loop.
        It will unblock the start() call.
        """
        self.app.exit()

    def getCurrentTrack(self):
        """
        Returns the currently playing Track.
        If the playlist is empty, returns None
        """
        if len(self._playlist) > 0:
            track =  self._playlist[self._playlistIdx]
            print "Current track is: {0}".format(track)
            return track
        return None

    def getFullState(self):
        mock = Mock(
            hasNextTrack = self.hasNextTrack(),
            hasPreviousTrack = self.hasPreviousTrack(),
            currentTime = self.player.currentTime(),
            state = self.getState(),
            currenTrack = str(self.getCurrentTrack())
        )
        return mock


class RemotePlayer(QtCore.QObject):
    """
    The RemotePlayer redirects all requests to an host using a RemoteClient
    """
    stateChanged = QtCore.Signal(str)

    #Emit a signal whenever the player source changes
    sourceChanged = QtCore.Signal(Track)

    ticked = QtCore.Signal(int)

    def __init__(self, host, port, remoteClient = None): 
       QtCore.QObject.__init__(self)
       if not remoteClient:
            self.remoteClient = RemoteClient(host, port)
       else :
            self.remoteClient = remoteClient

    def setRemoteClient(self,remoteClient):
        self.remoteClient = remoteClient

    def setParent(self, parent):
        print "Remote player has no use for a parent..."

    def seek(self, timeInMs):
        request = "player;seek;{0}".format(timeInMs)
        answer = self.remoteClient.sendRequest(request)
        return answer

    def setHeadless(self):
        print "Remote player has no use for a parent..."

    def currentPlaylist(self):
        print "Play list requested"
        return self._playlist 
    
    def hasNextTrack(self):
        request = 'player;hasNextTrack'
        result = bool(self.remoteClient.sendRequest(request))
        print result
        return result

    def hasPreviousTrack(self):
        request = 'player;hasPreviousTrack'
        return bool(self.remoteClient.sendRequest(request))

    def getCurrentTrack(self):
        request = 'player;getCurrentTrack'
        result = self.remoteClient.sendRequest(request)
        return Mock(eval(result))

    def playTrack(self, track):
        request = 'player;playTrack;{0}'.format(track)
        return self.remoteClient.sendRequest(request)

    def playTracks(self, tracks=[]):
        request = 'player;playTracks;{0}'.format(self._encodeTracks(tracks))
        return self.remoteClient.sendRequest(request)

    def queueTrack(self, track, emit=True):
        request = 'player;queueTrack;{0}'.format(track)
        return self.remoteClient.sendRequest(request)

    def queueTracks(self, tracks):
        request = 'player;queueTracks;{0}'.format(self._encodeTracks(tracks))
        return self.remoteClient.sendRequest(request)

    def playNextTrack(self):
        request = 'player;playNextTrack'
        return self.remoteClient.sendRequest(request)

    def playPreviousTrack(self):
        request = 'player;playPreviousTrack'
        return self.remoteClient.sendRequest(request)

    def stop(self):
        request = 'player;stop'
        return self.remoteClient.sendRequest(request)

    def resume(self):
        request = 'player;resume'
        return self.remoteClient.sendRequest(request)

    def pause(self):
        request = 'player;pause'
        return self.remoteClient.sendRequest(request)

    def getCurrentTime(self):
        request = 'player;getCurrentTime'
        return self.remoteClient.sendRequest(request)

    def getState(self):
        request = 'player;getFullState'
        return Mock(eval(self.remoteClient.sendRequest(request)))

    def togglePlayState(self):
        request = 'player;togglePlayState'
        return self.remoteClient.sendRequest(request)

    def notifyStateChanged(self):
        print "changed"

    def registerToStateChanges(self, target):
        request = 'player;registerToStateChanges;{0}'.format(target)
        return self.remoteClient.sendRequest(request)

    def unregisterToStateChanges(self, target):
        request = 'player;unregisterToStateChanges;{0}'.format(target)
        return self.remoteClient.sendRequest(request)
    
    def getFullState(self):
        request = 'player;getFullState'
        return Mock(eval(self.remoteClient.sendRequest(request)))

    def _encodeTracks(self,tracks):
        requestData = ""
        for track in tracks:
            requestData = requestData + str(track) + '|'
        requestData = requestData[:-1] #remove last |
        return requestData

def test():
    import time
    import content as content
    tracks = content.getTracks()

    player = RemotePlayer(qapp)
    player.playTrack(tracks[1])
    player.queueTrack(tracks[0])

    assert player.currentlyPlayingTrack() is tracks[1]

    time.sleep(5)
    player.playNextTrack()
    assert player.currentlyPlayingTrack() is tracks[0]

    sys.exit(qapp.exec_())    

if __name__ == "__main__":
    test()
