#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
play audio via phonon
"""
import sys
import os
from PySide import QtCore, QtGui
from PySide.QtCore import *
from PySide.QtGui import *

try:
    from PySide.phonon import Phonon
    #app = PySide.QtGui.QApplication(sys.argv)
    #app.setApplicationName('myname')
except ImportError:
    app = QtGui.QApplication(sys.argv)
    QtGui.QMessageBox.critical(None, "Music Player",
            "Your Qt installation does not have Phonon support.",
            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Default,
            QtGui.QMessageBox.NoButton)
    print "Your Qt installation does not have Phonon support."
    sys.exit(1)

class PlayerStates:
    STOPPED="STOPPED"
    PLAYING="PLAYING"
    PAUSED="PAUSED"
    ERROR = "ERROR"

class PhononPlayer(QtCore.QObject):
    stateChanged = QtCore.Signal()
    playerTicked = QtCore.Signal()

    _playlist = []
    _playlistIdx = 0

    def __init__(self, parent = None): 
       QtCore.QObject.__init__(self)
       if parent : 
          self.setParent(parent)

    def setParent(self, parent):
        self.app = parent
        self.audioOutput = Phonon.AudioOutput(Phonon.MusicCategory, parent)
        self.player = Phonon.MediaObject(parent)
        Phonon.createPath(self.player, self.audioOutput)
        self._bindEvents()

    def setHeadless(self):
        app = QCoreApplication(sys.argv)
        self.setParent(app)

    def currentPlaylist(self):
        print "Play list requested"
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


    def playTracks(self, tracks=[]):
        self._resetPlaylist()
        for track in tracks:
            self.queueTrack(track, emit=False)

        firstTrack = Phonon.MediaSource(self._playlist[self._playlistIdx].filePath)
        self.player.setCurrentSource(firstTrack)
        self.player.play()


    def playNextTrack(self):
        print "Playing next track..."
        if self.hasNextTrack():
            self._playlistIdx = self._playlistIdx + 1
            nextTrack = Phonon.MediaSource(self._playlist[self._playlistIdx].filePath)
            print nextTrack
            print self.player.setCurrentSource(nextTrack)
            print self.player.play()

    def playPreviousTrack(self):
        if self.hasPreviousTrack():
            self._playlistIdx = self._playlistIdx - 1
            previousTrack = Phonon.MediaSource(self._playlist[self._playlistIdx].filePath)
            self.player.setCurrentSource(previousTrack)
            self.player.play()


    def queueTrack(self, track, emit=True):
        print "Queuing track: ", track
        self._playlist.append(track)


    def queueTracks(self, tracks):
        for track in tracks:
            self.queueTrack(track, emit=False)

    def stop(self):
        print "Stopping player"
        self.player.stop()


    def resume(self):
        self.player.play()


    def pause(self):
        self.player.pause()

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

        return ""

    def togglePlayState(self):
        state = self.getState()
        if state == PlayerStates.PAUSED:
            self.resume()
        elif state == PlayerStates.PLAYING:
            self.pause()

    def notifyStateChanged(self):
        print "changed"

    def _stateChanged(self,state,state1):
        self.stateChanged.emit()

    def _sourceChanged(self, source):
        print "Player source changed", source
        self.stateChanged.emit()

    def _aboutToFinish(self):
        print "Player is about to finish playing the current track..."
        if self.hasNextTrack:
            self._playlistIdx = self._playlistIdx + 1
            nextTrack = Phonon.MediaSource(self._playlist[self._playlistIdx].filePath)
            self.player.enqueue(nextTrack)
        else:
            print "It was the last track, do nothing."

    def _bindEvents(self):
        self.connect(self.player, SIGNAL('tick(qint64)'), self._tick)
        self.connect(self.player, SIGNAL('stateChanged(Phonon::State, Phonon::State)'), self._stateChanged)
        self.connect(self.player, SIGNAL('currentSourceChanged(Phonon::MediaSource)'), self._sourceChanged)
        self.connect(self.player, SIGNAL('aboutToFinish()'), self._aboutToFinish)


    def _tick(self, time):
        displayTime = QtCore.QTime(0, (time / 60000) % 60, (time / 1000) % 60)
        self.playerTicked.emit()
        #print displayTime
        #self.timeLcd.display(displayTime.toString('mm:ss'))
    
    def _resetPlaylist(self):
        self._playlist = []
        self._playlistIdx = 0
        self.player.clearQueue()

    def start(self):
        self.app.exec_()

    state = QtCore.Property(QUrl, getState, notify=notifyStateChanged)

import socket 

class RemoteClient:
    def __init__(self):
        self.tcpIP = '192.168.1.127'
        self.tcpPort = 5005
        self.bufferSize = 1024

    def sendRequest(self, request):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.tcpIP, self.tcpPort))

        s.send(request)
        data = s.recv(self.bufferSize)
        #print "Server answered the client request...", data
        s.close()
        return ""

class RemotePlayer(QtCore.QObject):

    stateChanged = QtCore.Signal()
    playerTicked = QtCore.Signal()

    def __init__(self, parent = None): 
       QtCore.QObject.__init__(self)
       self.remoteClient = RemoteClient()

    def setParent(self, parent):
        print "Remote player has no use for a parent..."

    def setHeadless(self):
        print "Remote player has no use for a parent..."

    def currentPlaylist(self):
        print "Play list requested"
        return self._playlist 
    
    def hasNextTrack(self):
        request = '[player;hasNextTrack]'
        return self.remoteClient.sendRequest(request)
    
    def hasPreviousTrack(self):
        request = '[player;hasPreviousTrack]'
        return self.remoteClient.sendRequest(request)

    def currentlyPlayingTrack(self):
        request = '[player;currentlyPlayingTrack]'
        return self.remoteClient.sendRequest(request)

    def playTrack(self, track):
        request = '[player;playTrack;{0}]'.format(track)
        return self.remoteClient.sendRequest(request)

    def playTracks(self, tracks=[]):
        request = '[player;playTracks;{0}]'.format(self._encodeTracks(tracks))
        return self.remoteClient.sendRequest(request)

    def queueTrack(self, track, emit=True):
        request = '[player;queueTrack;{0}]'.format(track)
        return self.remoteClient.sendRequest(request)

    def queueTracks(self, tracks):
        request = '[player;queueTracks;{0}]'.format(self._encodeTracks(tracks))
        return self.remoteClient.sendRequest(request)

    def playNextTrack(self):
        request = '[player;playNextTrack]'
        return self.remoteClient.sendRequest(request)

    def playPreviousTrack(self):
        request = '[player;playPreviousTrack]'
        return self.remoteClient.sendRequest(request)

    def stop(self):
        request = '[player;stop]'
        return self.remoteClient.sendRequest(request)

    def resume(self):
        request = '[player;resume]'
        return self.remoteClient.sendRequest(request)

    def pause(self):
        request = '[player;pause]'
        return self.remoteClient.sendRequest(request)

    def getCurrentTime(self):
        request = '[player;getCurrentTime]'
        return self.remoteClient.sendRequest(request)

    def getState(self):
        request = '[player;getState]'
        return self.remoteClient.sendRequest(request)

    def togglePlayState(self):
        request = '[player;togglePlayState]'
        return self.remoteClient.sendRequest(request)

    def notifyStateChanged(self):
        print "changed"
    
    def _encodeTracks(self,tracks):
        requestData = "["
        for track in tracks:
            requestData = requestData + str(track) + '|'
        requestData = requestData[:-1] #remote last |
        requestData = requestData + "]"
        return requestData

def test():
    import time
    import content as content
    tracks = content.getTracks()

    qapp=QtGui.QApplication(sys.argv)
    player = PhononPlayer(qapp)
    player.playTrack(tracks[1])
    player.queueTrack(tracks[0])

    assert player.currentlyPlayingTrack() is tracks[1]

    time.sleep(5)
    player.playNextTrack()
    assert player.currentlyPlayingTrack() is tracks[0]

    sys.exit(qapp.exec_())    

if __name__ == "__main__":
    test()
