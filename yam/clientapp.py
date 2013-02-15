#!../bin/python
"""
Calling this module creates the client portion
of the mediacenter.

TODO: Split most ui components in a new yam/ui/ subfolder
"""
import logging
import sys

from PySide import QtDeclarative
from PySide.QtCore import *
import PySide.QtCore as QtCore
from PySide.QtDeclarative import QDeclarativeView
from PySide.QtGui import *
import PySide.QtGui as QtGui
import config as config
import content as content
from content import Mock
from devices import DeviceManager, Device, DeviceWatcher
import player as players
from profiling import profile
import os

print "Running with vm: {0}".format(sys.executable)

APP = None

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    @profile
    def initUI(self):
        self.currentView = DefaultMusicCollectionView(self)
        self.centerStackedWidget = QStackedWidget()

        self.centerStackedWidget.addWidget(self.currentView)
        self.setCentralWidget(self.centerStackedWidget)

        self.setGeometry(0,0,1680,1050)

        musicAction = QtGui.QAction(QtGui.QIcon('../art/Music.png'), 'Show music collection', self)
        musicAction.triggered.connect(self.showDefaultMusicView)

        configureAction = QtGui.QAction(QtGui.QIcon('../art/Tools.png'), 'Configure YAM', self)
        configureAction.triggered.connect(self.showConfigPanel)

        devicesAction = QtGui.QAction(QtGui.QIcon('../art/Network.png'), 'Show availaible devices', self)
        devicesAction.triggered.connect(self.showDevicesPanel)

        fileErrorsAction = QtGui.QAction(QtGui.QIcon('../art/Info.png'), 'Show last index report', self)
        fileErrorsAction.triggered.connect(self.showIndexReport)

        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(musicAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(configureAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(devicesAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(fileErrorsAction)
        self.toolbar.setIconSize(QtCore.QSize(60,60))

        dark = "#2D2D2D"
        style_str = "QWidget {background-color: %s}"
        self.toolbar.setStyleSheet(style_str % dark)

        self.setWindowTitle('YAM')

    def showConfigPanel(self):
        wizard = ConfigurationWizard()
        wizard.exec_()
        self.showDefaultMusicView()

    def showDefaultMusicView(self):
        self.centerStackedWidget.removeWidget(self.currentView)
        self.currentView = DefaultMusicCollectionView(self)
        self.centerStackedWidget.addWidget(self.currentView)

    def showIndexReport(self):
        self.centerStackedWidget.removeWidget(self.currentView)
        self.currentView = IndexReportView(self)
        self.centerStackedWidget.addWidget(self.currentView)

    def showDevicesPanel(self):
        deviceManPanel = DeviceManagementPanel()
        deviceManPanel.exec_()

    def show_and_raise(self):
        self.show()
        self.raise_()

        if not config.workspaceIsSet():
            self.showConfigPanel()



class IndexReportView(QtGui.QWidget):
    def __init__(self, parent=None):
        QtCore.QObject.__init__(self)
        self.initUI()

    def initUI(self):
        pass

    def show_and_raise(self):
        self.show()
        self.raise_()


class DeviceManagementPanel(QtGui.QDialog):
    def __init__(self, parent=None):
        super(DeviceManagementPanel, self).__init__(parent)
        self.initUI()

    def initUI(self):
        mainLayout = QtGui.QVBoxLayout()

        self.deviceListView = DeviceList()
        mainLayout.addWidget(self.deviceListView)

        applyButton = QtGui.QPushButton("Choose")
        applyButton.clicked.connect(self.applyChanges)
        applyButton.setDefault(True)

        closeButton = QtGui.QPushButton("Cancel")
        closeButton.clicked.connect(self.tryClose)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addWidget(closeButton)
        buttonLayout.addWidget(applyButton)
        mainLayout.addLayout(buttonLayout)

        self.setWindowTitle('Choose a device to control')
        self.setLayout(mainLayout)

        self.deviceListView.selectActiveDevice()

    def tryClose(self):
        print "Closing device manager..."
        self.close()

    def applyChanges(self):
        print "Applying changes to DeviceManager..."
        selectedDevice = self.deviceListView.selectedDevice
        if selectedDevice:
            global APP
            APP.deviceMan.setActiveDevice(selectedDevice)
            APP.updatePlayer()
            self.tryClose()
        else :
            print "No device selected. Cannot apply changes."

class ConfigurationWizard(QtGui.QWizard):
    def __init__(self, parent=None):
        super(ConfigurationWizard, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.addPage(self.createIntroPage())
        self.addPage(self.createRegistrationPage())
        self.addPage(self.createLibraryLocationPage())
        self.addPage(self.createConclusionPage())

        self.setWindowTitle("YAM setup")

    def show_and_raise(self):
        self.show()
        self.raise_()

    def createIntroPage(self):
        page = QtGui.QWizardPage()
        page.setTitle("Introduction")

        label = QtGui.QLabel("This wizard will help you set the YAM client.")
        label.setWordWrap(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        page.setLayout(layout)

        return page

    def createLibraryLocationPage(self):
        page = QtGui.QWizardPage()
        page.setTitle("Import music")
        page.setSubTitle("Where is your music ?")

        self.configLocationDialog = QtGui.QPushButton("Folder:")
        self.configLocationDialog.clicked.connect(self._showLibraryDialog)

        self.libraryDirectoryEdit = QtGui.QLineEdit()
        self.libraryDirectoryEdit.setText(config.getProperty('music_library_folder'))
        self.libraryDirectoryEdit.textChanged.connect(self._handleLibraryPathChanged)

        self.indexLibraryButton = QPushButton("Index folder")
        self.indexLibraryButton.clicked.connect(self._indexLibrary)

        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.configLocationDialog, 0, 0)
        layout.addWidget(self.libraryDirectoryEdit, 0, 1)
        layout.addWidget(self.indexLibraryButton, 1, 0)
        layout.addWidget(self.progressBar,1,1)
        page.setLayout(layout)
        page.initializePage = self.initLibraryLocationPage

        return page

    def _handleLibraryPathChanged(self, newPath):
        print newPath
        if os.path.isdir(newPath):
            self.indexLibraryButton.setEnabled(True)
        else :
            self.indexLibraryButton.setEnabled(False)

    def initLibraryLocationPage(self):
        self.libraryDirectoryEdit.setText(config.getProperty('music_library_folder'))


    def createRegistrationPage(self):
        page = QtGui.QWizardPage()
        page.setTitle("Select a workspace")
        page.setSubTitle("YAM stores application data, configuration files and user data into the workspace.")

        configLocationDialog = QtGui.QPushButton("Workspace:")
        configLocationDialog.clicked.connect(self._showFolderDialog)

        self.directoryEdit = QtGui.QLineEdit()
        self.directoryEdit.textChanged.connect(self._workspaceValueChanged)
        self.directoryEdit.setText(config.getWorkspaceLocation())
        layout = QtGui.QGridLayout()
        layout.addWidget(configLocationDialog, 0, 0)
        layout.addWidget(self.directoryEdit, 0, 1)
        page.setLayout(layout)

        return page

    def _workspaceValueChanged(self, sender):
            workspace = self.directoryEdit.text()
            print "Setting workspace location:", workspace
            config.setWorkspaceLocation(workspace)

    def _showFolderDialog(self):
        options = QtGui.QFileDialog.DontResolveSymlinks | QtGui.QFileDialog.ShowDirsOnly
        directory = QtGui.QFileDialog.getExistingDirectory(self,
                "QFileDialog.getExistingDirectory()",
                self.directoryEdit.text(), options)
        if directory:
            self.directoryEdit.setText(directory)


    def _showLibraryDialog(self):
        options = QtGui.QFileDialog.DontResolveSymlinks | QtGui.QFileDialog.ShowDirsOnly
        directory = QtGui.QFileDialog.getExistingDirectory(self,
                "QFileDialog.getExistingDirectory()",
                self.libraryDirectoryEdit.text(), options)
        if directory:
           self.libraryDirectoryEdit.setText(directory)

    def _indexLibrary(self):
        self.configLocationDialog.setEnabled(False)
        self.libraryDirectoryEdit.setEnabled(False)
        musicLibraryFolder = self.libraryDirectoryEdit.text().encode("utf-8")
        musicLibraryFolder = musicLibraryFolder + "/"
        self.task = content.LibraryIndexationTask(musicLibraryFolder)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(self.task.getWorkload())
        QtCore.QObject.connect(self.task, QtCore.SIGNAL("progress(int)"),self.progressBar, QtCore.SLOT("setValue(int)"), QtCore.Qt.QueuedConnection)
        if not self.task.isRunning():
            self.task.exiting = False
            self.task.start()

    def createConclusionPage(self):
        page = QtGui.QWizardPage()
        page.setTitle("Conclusion")

        label = QtGui.QLabel("You have successfully set the YAM client. Have a nice day!")
        label.setWordWrap(True)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        page.setLayout(layout)

        return page

    def accept(self):
        print "Saving configuration changes..."

        workFolder = self.directoryEdit.text().encode("utf-8")
        print "Setting workspace location:", workFolder
        config.writeWorkspaceLocation(workFolder)

        musicLibraryFolder = self.libraryDirectoryEdit.text().encode("utf-8")
        print "Setting music library location:", musicLibraryFolder
        config.setProperty(config.Properties.MUSIC_LIBRARY, musicLibraryFolder)

        print "Settings were changed."
        APP.mainWin.showDefaultMusicView()
        APP.updatePlayer()
        return self.done(0)


class DeviceList(QtGui.QListView):

        def __init__(self):
            super(DeviceList, self).__init__()
            self.initUI()
            self.bindEvents()
            self.loadDevices()
            self.selectedDevice = APP.deviceMan.getActiveDevice()

        def initUI(self):
            self.setMaximumHeight(240)
            self.setIconSize(QtCore.QSize(80, 80))

        def bindEvents(self):
            pass

        def keyPressEvent(self, event):
            key = event.key()
            print "Device list received KeyPressed event: ", key

            if key == QtCore.Qt.Key_Return:
                return
            elif key == QtCore.Qt.Key_Left:
                return
            elif key == QtCore.Qt.Key_Right:
                return
            elif key == QtCore.Qt.Key_Up:
                currentRow = self.currentRow()
                if currentRow > 0:
                    currentRow = currentRow - 1
                    self.setCurrentRow(currentRow)
                return
            elif key == QtCore.Qt.Key_Down:
                currentRow = self.currentRow()
                if currentRow < (self.count() - 1):
                    currentRow = currentRow + 1
                    self.setCurrentRow(currentRow)
                return
            else:
                return super(QListWidget, self).keyPressEvent(event)

        def loadDevices(self):
            print "Loading devices into listview..."
            self.devices = APP.deviceMan.getDevices()
            self.devicesWithIcon = []
            for device in self.devices:
                deviceName = repr(device)
                art = None
                print deviceName
                if 'rpi' in deviceName:
                    art = '../art/rpi.png'
                elif device.type == "local":
                    import platform
                    if "Linux" == platform.system():
                        art = '../art/linux.ico'
                if art == None:
                    art ='../art/nocover1.jpg'
                model = repr(device) , art
                self.devicesWithIcon.append(model)

            list_model = ListModel(self.devicesWithIcon)
            self.setModel(list_model)

        def selectActiveDevice(self):
            for device in self.devices:
                if device == self.selectedDevice:
                    pass
            #items = self.findItems("*")


        def selectionChanged(self, newSelection, oldSelection):
            selectedIdx = newSelection.indexes()[0].row()
            self.selectedDevice = self.devices[selectedIdx]
            print "The device '{0}' was selected from the list.".format(self.selectedDevice.visibleName)



class ListModel(QtCore.QAbstractListModel):
    def __init__(self, os_list):
        super(ListModel, self).__init__()
        self.os_list = os_list

    def rowCount(self, parent):
        if not self.os_list: return 0
        return len(self.os_list)

    def data(self, index, role = QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        os_name, os_logo_path = self.os_list[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return os_name
        elif role == QtCore.Qt.DecorationRole:
            if not os_logo_path or os_logo_path == "" or os_logo_path == None:
                os_logo_path = '../art/nocover1.jpg'
            return QtGui.QIcon("")

        return None



class TrackTable(QtGui.QTableWidget):

        def __init__(self):
            super(TrackTable, self).__init__()
            self.initUI()
            self.bindEvents()

        def initUI(self):
            self.setColumnCount(5)
            self.setSortingEnabled(True)
            self.setAlternatingRowColors(True)
            self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
            self.setAutoScroll(True)
            self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
            self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)

        def bindEvents(self):
            self.itemDoubleClicked.connect(self.trackClicked)

        def keyPressEvent(self, event):
            key = event.key()
            print "Track table received KeyPressed event: ", key
            if key == QtCore.Qt.Key_P or key == QtCore.Qt.Key_Return:
                self._playTrack(self.currentItem().row())
                return
            elif key == QtCore.Qt.Key_Q:
                self._queueTrack(self.currentItem().row())
                return
            elif key == QtCore.Qt.Key_S:
                APP.player.stop()
                return
            elif key == QtCore.Qt.Key_Left:
                self.focusPreviousChild()
                return
            elif key == QtCore.Qt.Key_Right:
                self.focusNextChild()
                return
            elif key == QtCore.Qt.Key_Space:
                APP.player.togglePlayState()
                return
            elif key == QtCore.Qt.Key_N:
                APP.player.playNextTrack()
                return
            elif key == QtCore.Qt.Key_Up:
                currentRow = self.currentRow()
                if currentRow > 0:
                    currentRow = currentRow - 1
                    self.setCurrentCell(currentRow, 0)
                else:
                    self.focusPreviousChild()
                return
            elif key == QtCore.Qt.Key_Down:
                currentRow = self.currentRow()
                if currentRow  < (self.rowCount() - 1):
                    currentRow = currentRow + 1
                    self.setCurrentCell(currentRow, 0)
                else:
                    self.setCurrentCell(0, 0)
                return
            else:
                QtGui.QWidget.keyPressEvent(self, event)

        def trackClicked(self, clickedItem):
            row = clickedItem.row()
            self._playTrack(row)

        def _playTrack(self, row):
            track = self._findTrack(row)
            if APP.player and track:
                APP.player.playTrack(track)

        def _queueTrack(self, row):
            track = self._findTrack(row)
            if not track == None:
                APP.player.queueTrack(track)

        def _findTrack(self, row):
            trackTitle = self.item(row,1).text()
            print "Looking for track with title: ", trackTitle

            tracksWithTitle = filter(lambda x:x.title == trackTitle, self.tracks)
            if len(tracksWithTitle) > 0:
                track = tracksWithTitle[0]
                return track
            return None

        def setHeader(self, _labels = None):
            labels = ('Track', 'Title','Artist','Album', 'Time')
            self.setHorizontalHeaderLabels(labels)
            self.horizontalHeader().setStretchLastSection(True)
            self.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
            self.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
            self.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
            self.horizontalHeader().setResizeMode(3, QtGui.QHeaderView.ResizeToContents)
            self.horizontalHeader().setResizeMode(4, QtGui.QHeaderView.ResizeToContents)

        def setTracks(self, data):
            print "Loading tracks into track table...", str(len(data))
            self.tracks = data
            self.clear()
            self.setRowCount(len(data))
            row = 0
            for track in data:
                self.setItem(row, 0, QTableWidgetItem(track.num ,0))
                self.setItem(row, 1, QTableWidgetItem(track.title ,1))
                self.setItem(row, 2, QTableWidgetItem(track.artist, 2))
                self.setItem(row, 3, QTableWidgetItem(track.albumTitle, 3))
                self.setItem(row, 4, QTableWidgetItem("{:4.2f}".format(track.lengthMS/60), 4))
                row = row + 1
            self.setHeader()



class AlbumList(QtGui.QListWidget):

        albumClicked = QtCore.Signal(str)

        def __init__(self):
            super(AlbumList, self).__init__()
            self.initUI()
            self.bindEvents()

        def initUI(self):
            self.setMaximumHeight(200)

        def bindEvents(self):
            self.itemClicked.connect(self._albumClicked)

        def keyPressEvent(self, event):
            key = event.key()
            print "Album list received KeyPressed event: ", key

            if key == QtCore.Qt.Key_P:
                albumTitle = self.item(self.currentRow()).text()
                self._playAlbum(albumTitle)
                return
            elif key == QtCore.Qt.Key_Return:
                self._albumClicked(self.currentItem())
                return
            elif key == QtCore.Qt.Key_Q:
                albumTitle = self.item(self.currentRow()).text()
                self._queueAlbum(albumTitle)
                return
            elif key == QtCore.Qt.Key_S:
                APP.player.stop()
                return
            elif key == QtCore.Qt.Key_Space:
                APP.player.togglePlayState()
                return
            elif key == QtCore.Qt.Key_Left:
                self.focusPreviousChild()
                return
            elif key == QtCore.Qt.Key_Right:
                self.focusNextChild()
                return
            elif key == QtCore.Qt.Key_Up:
                currentRow = self.currentRow()
                if currentRow > 0:
                    currentRow = currentRow - 1
                    self.setCurrentRow(currentRow)
                else:
                    self.focusPreviousChild()
                self._albumClicked(self.currentItem())
                return
            elif key == QtCore.Qt.Key_Down:
                currentRow = self.currentRow()
                if currentRow < (self.count() - 1):
                    currentRow = currentRow + 1
                    self.setCurrentRow(currentRow)
                else:
                    self.focusNextChild()
                self._albumClicked(self.currentItem())
                return
            else:
                return super(QListWidget, self).keyPressEvent(event)

        def setAlbums(self, tracks):
            print "Loading albums into listview..."
            self.clear()
            self.tracks = tracks
            albums = content.getAlbums(tracks)

            index = 0
            headerText = "All albums (" + str(len(albums)) + ")"
            header = QListWidgetItem(headerText)
            self.insertItem(0, header)

            index = index + 1
            for album in albums:
                item = QListWidgetItem(album)
                self.insertItem(index, item)
                index = index + 1

        def _albumClicked(self, albumRowModel):
            pass

        def _playAlbum(self, albumTitle):
            tracks = self._getTracksForSelectedAlbum(albumTitle)
            if APP.player:
                APP.player.playTracks(tracks)

        def _queueAlbum(self, albumTitle):
            tracks = self._getTracksForSelectedAlbum(albumTitle)
            APP.player.queueTracks(tracks)

        def _getTracksForSelectedAlbum(self, albumTitle):
            tracksForAlbum = content.getTracksForAlbum(albumTitle, self.tracks)
            return tracksForAlbum

        def selectionChanged(self, newSelection, oldSelection):
            self.albumClicked.emit(self.currentItem().text())


class ArtistList(QtGui.QListView):
     artistClicked = QtCore.Signal(QModelIndex)
     def __init__(self):
        super(ArtistList, self).__init__()
        self.artistsAndCovers = None
        self.allArtistsEntry  = None
        self.initUI()
        self.bindEvents()

     def initUI(self):
        self.setIconSize(QtCore.QSize(55, 55))
        #self.setSpacing(5)
        self.setUniformItemSizes(True)
        self.setMaximumWidth(300)

     def bindEvents(self):
        pass


     def setArtists(self, artistsAndCovers):
        self.artistsAndCovers = artistsAndCovers
        if self.artistsAndCovers and len(self.artistsAndCovers) > 0:
            firstEntry = self.artistsAndCovers[0]
            if isinstance(firstEntry, list):
                self.allArtistsEntry = ('All {0} artists'.format(len(artistsAndCovers)),"")
                self.artistsAndCovers.insert(0, self.allArtistsEntry)

        list_model = ListModel(self.artistsAndCovers)
        self.setModel(list_model)


     def _getNextArtistQIndex(self):
        if len(self.selectedIndexes()) > 0:
            currentArtist = self.selectedIndexes()[0]
            if currentArtist.row() < (len(self.artistsAndCovers)  - 1):
                nextArtist = currentArtist.sibling(currentArtist.row() + 1,0)
                return nextArtist
        return None

     def _getPreviousArtistQIndex(self):
        if len(self.selectedIndexes()) > 0:
            currentArtist = self.selectedIndexes()[0]
            if currentArtist.row() > 0:
                previousArtist = currentArtist.sibling(currentArtist.row() - 1,0)
                return previousArtist
        return None

     def selectionChanged(self, newSelection, oldSelection):
         self.artistClicked.emit(newSelection.indexes()[0])


class PlayerStatusPanel(QtGui.QWidget):
        """The PlayerStatusPanel can :

            Keep track of the active Player.

            Display information about the Player's state.

            Send commands to the active Player.
        """
        def __init__(self, parent = None):
            super(PlayerStatusPanel, self).__init__(parent)
            self.player = APP.player
            self.currenTrack = None
            self.initUI()
            self.bindEvents()
            self.refreshState()

        def initUI(self):
            self.setupActions()
            self.setupUi()

        def bindEvents(self):
            APP.playerChanged.connect(self._onPlayerChanged)

            self._bindToPlayerSignals()


        def _onSliderPressed(self):
            self.sliding = True

        def _onPlayerChanged(self):
            self.player = APP.player
            self._bindToPlayerSignals()
            self.refreshState(self.player.getCurrentTrack())

        def _bindToPlayerSignals(self):
            if not self.player:
                return

            self.player.stateChanged.connect(self._onPlayerStateChanged)
            self.player.ticked.connect(self._onPlayerTicked)
            self.playAction.triggered.connect(self.player.togglePlayState)
            self.pauseAction.triggered.connect(self.player.togglePlayState)
            self.nextAction.triggered.connect(self.player.playNextTrack)
            self.previousAction.triggered.connect(self.player.playPreviousTrack)
            self.timeLcd.sliderReleased.connect(self._onSliderReleased)
            self.timeLcd.sliderPressed.connect(self._onSliderPressed)

        def _onSliderReleased(self):
            self.sliding = False
            self.player.seek(self.timeLcd.value()*1000)

        def _onPlayerTicked(self, timeSinceBegingInSec):
            if not self.sliding:
                self.timeLcd.setValue(timeSinceBegingInSec/1000)

        def _onPlayerStateChanged(self):
            fullState = self.player.getFullState()
            #self.currenTrack = Mock(eval(fullState.currentTrack()))
            self.currenTrack = self.player.getCurrentTrack()
            self.refreshState(self.currenTrack)
            self.playAction.setEnabled(fullState.state == "PAUSED")
            self.pauseAction.setEnabled(fullState.state == "PLAYING")
            self.nextAction.setEnabled(fullState.hasNextTrack)
            self.previousAction.setEnabled(fullState.hasPreviousTrack)
            #self.timeLcd.setValue(fullState.currentTime)

        def setupActions(self):
            self.playAction = QtGui.QAction(QIcon('../art/Play.png'), "Play" ,self)
            self.pauseAction = QtGui.QAction(QIcon('../art/Pause.png'), "Pause", self)
            self.nextAction = QtGui.QAction(QIcon('../art/NextTrack.png'),"Play next track", self)
            self.previousAction = QtGui.QAction(QIcon('../art/PreviousTrack.png'),"Play previous track", self)

        def setupUi(self):

            self.currentPlayerLabel = QLabel()
            fontPlayerLabel = self.currentPlayerLabel.font()
            fontPlayerLabel.setPointSize(18)
            fontPlayerLabel.setBold(True)
            self.currentPlayerLabel.setFont(fontPlayerLabel)
            self.currentPlayerLabel.setStyleSheet("QLabel { color : black; }")

            self.imgLabel = QLabel()
            self.imgLabel.setFixedSize(QSize(300,300))

            self.trackTitleLabel = QLabel()
            fontTrackTitleLabel = self.trackTitleLabel.font()
            fontTrackTitleLabel.setPointSize(8)
            fontTrackTitleLabel.setBold(False)
            self.trackTitleLabel.setStyleSheet("QLabel { color : black; }")
            self.trackTitleLabel.setFont(fontTrackTitleLabel)

            albumAndArtistLay = QVBoxLayout()

            self.albumTitleLabel = QLabel()
            fontAlbumLabel = self.albumTitleLabel.font()
            fontAlbumLabel.setPointSize(18)
            fontAlbumLabel.setBold(True)
            self.albumTitleLabel.setFont(fontAlbumLabel)
            self.albumTitleLabel.setStyleSheet("QLabel { color : black; }")

            self.artistNameLabel = QLabel()
            fontArtistLabel =  self.artistNameLabel.font()
            fontArtistLabel.setPointSize(14);
            fontArtistLabel.setBold(False)
            self.artistNameLabel.setFont(fontArtistLabel)
            self.artistNameLabel.setStyleSheet("QLabel { color : black; }")

            albumAndArtistLay.addWidget(self.albumTitleLabel)
            albumAndArtistLay.addWidget(self.artistNameLabel)


            self.timeLcd = QtGui.QSlider()
            self.timeLcd.setOrientation(Qt.Horizontal)

            bar = QToolBar()
            bar.addSeparator()
            bar.addAction(self.previousAction)
            bar.addSeparator()
            bar.addAction(self.playAction)
            bar.addSeparator()
            bar.addAction(self.pauseAction)
            bar.addSeparator()
            bar.addAction(self.nextAction)
            bar.addSeparator()
            bar.setIconSize(QtCore.QSize(45,45))

            dark = "#2D2D2D"
            style_str = "QWidget {background-color: %s}"
            bar.setStyleSheet(style_str % dark)

            mainLayout = QtGui.QVBoxLayout()
            mainLayout.addWidget(self.currentPlayerLabel)
            mainLayout.addWidget(bar)
            mainLayout.addWidget(self.trackTitleLabel)
            mainLayout.addWidget(self.timeLcd)
            mainLayout.addWidget(self.imgLabel)
            mainLayout.addLayout(albumAndArtistLay)

            mainLayout.addStretch()
            self.sliding = False
            self.setLayout(mainLayout)
            self.setMaximumWidth(300)

        def refreshState(self, track=None):
            activeDevice = APP.deviceMan.getActiveDevice()
            if activeDevice:
                self.currentPlayerLabel.setText(activeDevice.visibleName)

            if track:
                pixmap = QPixmap(track.albumCoverPath).scaledToHeight(300)
                self.imgLabel.setPixmap(pixmap)
                self.imgLabel.setFixedSize(QSize(300,300))
                self.albumTitleLabel.setText(track.albumTitle)
                self.artistNameLabel.setText(track.artist)
                self.trackTitleLabel.setText(track.title)
                self.timeLcd.setMaximum(int(track.lengthMS))

class DefaultMusicCollectionView(QtGui.QWidget):

     def __init__(self, parent = None):
        super(DefaultMusicCollectionView, self).__init__(parent)
        self.tracks = content.getTracks()
        self.initUI()
        self.bindEvents()

     def initUI(self):
        #Prepare main layout
        hbox = QtGui.QHBoxLayout(self)
        self.setLayout(hbox)

        #Prepare artist view
        self.artistsView = ArtistList()
        hbox.addWidget(self.artistsView)
        self.artistsAndCovers = content.getArtistsWithRandomCover()
        self.artistsView.setArtists(self.artistsAndCovers)

        #Prepare right layout
        self.rightPanel = QWidget()
        self.rightVBox = QVBoxLayout()
        self.rightPanel.setLayout(self.rightVBox)
        hbox.addWidget(self.rightPanel)

        #Prepare albums view
        self.albumsView = AlbumList()
        self.albumsView.setAlbums(self.tracks)

        self.topHBox = QHBoxLayout()

        self.visibleCoverLabel = QLabel("No album selected")
        pixmap = QPixmap("../art/nocover1.jpg")
        if pixmap:
            self.visibleCoverLabel.setPixmap(pixmap)
        self.visibleCoverLabel.setFixedSize(QSize(200,200))

        self.topHBox.addWidget(self.visibleCoverLabel)
        self.topHBox.addWidget(self.albumsView)
        self.rightVBox.addLayout(self.topHBox)

        #Prepare tracks view
        self.tracksTable = TrackTable()
        self.tracksTable.setHeader()
        self.rightVBox.addWidget(self.tracksTable)

        #Prepare PlayerStatusView
        self.playerStatus = PlayerStatusPanel()
        hbox.addWidget(self.playerStatus)


     def bindEvents(self):
        #self.albumsView.albumClicked.connect(self.playerStatus.showAlbum)
        self.artistsView.artistClicked.connect(self.artistClicked)
        self.albumsView.albumClicked.connect(self.albumClicked)


     def albumClicked(self, albumTitle):
        tracksForAlbum = content.getTracksForAlbum(albumTitle, self.tracks)
        self.tracksTable.close()
        self.rightVBox.removeWidget(self.tracksTable)
        self.tracksTable = TrackTable()
        self.tracksTable.setTracks(tracksForAlbum)

        self.rightVBox.addWidget(self.tracksTable)

        cover = tracksForAlbum[0].albumCoverPath
        pixmap = QPixmap(cover).scaledToHeight(200)
        self.visibleCoverLabel.setPixmap(pixmap)

     def artistClicked(self, artistRowModel):
        artistName, cover = self.artistsAndCovers[artistRowModel.row()]
        print "Clicked on artist: ", artistName

        albumsForArtist = filter(lambda x:x.artist == artistName, self.tracks)
        self.albumsView.setAlbumssocket.settimeout(value)(albumsForArtist)

        pixmap = QPixmap(cover).scaledToHeight(200)
        self.visibleCoverLabel.setPixmap(pixmap)


class Client(QtCore.QObject):

    playerChanged = QtCore.Signal()

    def __init__(self, showApp=False):
        QtCore.QObject.__init__(self)
        self.showApp = showApp
        self.player = None
        self.deviceMan = DeviceManager(startWatcher=True)
        self.updatePlayer()

    def init(self):
        try:
            self.app = QtGui.QApplication(sys.argv)
        except RuntimeError:
            self.app = QtCore.QCoreApplication.instance()
        self.app.setApplicationName('yamclient')
        self.mainWin = MainWindow()
        self.bindEvents()
        self.deviceStateChangeWatcher = DeviceWatcher(portToWatch=5556, callback=self.playerStateChanged)
        self.deviceStateChangeWatcher.start()


    def bindEvents(self):
        self.app.aboutToQuit.connect(self.stop)

    def updatePlayer(self):
        activeDevice = self.deviceMan.getActiveDevice()

        if activeDevice:
            self.player = players.getPlayerByType(activeDevice)
            self.player.registerToStateChanges(activeDevice.host)
            self.playerChanged.emit()

    def playerStateChanged(self, state):
        self.player.stateChanged.emit(state)

    def start(self):
        try:
            if self.showApp:
                self.mainWin.show_and_raise()
            # Enter Qt application main loop
            self.app.exec_()
        except (KeyboardInterrupt, SystemExit):
            pass

    def close(self):
        #TODO : Remove
        self.deviceMan.dispose()
        self.app.exit()
        self.player.stop()

    def stop(self):
        if self.deviceMan: self.deviceMan.dispose()
        if self.app: self.app.exit()
        if self.player: self.player.stop()

def main(argv=None):
    client = setupClient()
    client.start()

def setupTestClient():
    client = Client(showApp=False)
    client.init()
    global APP
    APP = client
    return client

def setupClient():
    global APP
    APP = Client(showApp=True)
    APP.init()
    return APP

if __name__ == '__main__':
    sys.exit(main())