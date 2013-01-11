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
        self.audioOutput = Phonon.AudioOutput(Phonon.MusicCategory, parent)
        self.player = Phonon.MediaObject(parent)
        Phonon.createPath(self.player, self.audioOutput)
        self._bindEvents()

    @Slot(result='QVariant')
    def currentPlaylist(self):
        print "Play list requested"
        return self._playlist 
    
    @Slot(result=bool)
    def hasNextTrack(self):
        return self._playlistIdx < len(self._playlist) - 1
    
    @Slot(result=bool)
    def hasPreviousTrack(self):
        return  self._playlistIdx > 0

    @Slot(result='QVariant')
    def currentlyPlayingTrack(self):
        return self._playlist[self._playlistIdx]

    @Slot('QVariant')
    def playTrack(self, track):
        self._resetPlaylist()

        trackPath = os.path.realpath(track.filePath)
        print "Playing track: ", track
        
        self.player.setCurrentSource(Phonon.MediaSource(trackPath))
        self._playlist.append(track)
        self.player.play()

    @Slot('QVariant')
    def playTracks(self, tracks=[]):
        self._resetPlaylist()
        for track in tracks:
            self.queue(track, emit=False)

        firstTrack = Phonon.MediaSource(self._playlist[self._playlistIdx].filePath)
        self.player.setCurrentSource(firstTrack)
        self.player.play()

    @Slot()
    def playNextTrack(self):
        if self.hasNextTrack():
            self._playlistIdx = self._playlistIdx + 1
            nextTrack = Phonon.MediaSource(self._playlist[self._playlistIdx].filePath)
            self.player.setCurrentSource(nextTrack)
            self.player.play()

    @Slot()
    def playPreviousTrack(self):
        if self.hasPreviousTrack():
            self._playlistIdx = self._playlistIdx - 1
            previousTrack = Phonon.MediaSource(self._playlist[self._playlistIdx].filePath)
            self.player.setCurrentSource(previousTrack)
            self.player.play()

    @Slot()
    def queue(self, track, emit=True):
        print "Queuing track: ", track
        self._playlist.append(track)

    @Slot()
    def queueTracks(self, tracks):
        for track in tracks:
            self.queue(track, emit=False)

    @Slot()
    def stop(self):
        print "Stopping player"
        self.player.stop()

    @Slot()
    def resume(self):
        self.player.play()

    @Slot()
    def pause(self):
        self.player.pause()

    @Slot(result='double')
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
        if self.hasNextTrack:
            self._playlistIdx = self._playlistIdx + 1
            nextTrack = Phonon.MediaSource(self._playlist[self._playlistIdx].filePath)
            self.player.enqueue(nextTrack)

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

    state = QtCore.Property(QUrl, getState, notify=notifyStateChanged)

            


def test():
    import time
    import content as content
    tracks = content.getTracks()

    qapp=QtGui.QApplication(sys.argv)
    player = PhononPlayer(qapp)
    player.playTrack(tracks[1])
    player.queue(tracks[0])

    assert player.currentlyPlayingTrack() is tracks[1]

    time.sleep(5)
    player.playNextTrack()
    assert player.currentlyPlayingTrack() is tracks[0]

    sys.exit(qapp.exec_())    

if __name__ == "__main__":
    test()
