
import logging
import config as config
import cPickle as json
from urllib import *
from profiling import profile
from PySide.QtCore import *
from PySide.QtGui import *
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import os

class Mock(object):
     def __init__(self, dictCopy=None, **kwargs):
         self.__dict__.update(kwargs)
         if dictCopy != None:
            self.__dict__ = dictCopy

     def __repr__(self):
        return str(self.__dict__)

     def __str__(self):
        return str(self.__dict__)

VIEWS = {}

class Track:
    def __init__(self):
        self.title = ""
        self.artist = ""
        self.albumTitle= ""
        self.lengthMS = ""
        self.num = ""
        self.albumCoverPath = "" 
        self.filePath = ""

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

@profile
def getAlbums(_tracks = None):
    tracks = _tracks or load()
    albums = []

    if tracks:
        for track in tracks:
            album = track.albumTitle
            if not album in albums:
                albums.append(album)
    return sorted(albums)


def getArtistsWithRandomCover(_tracks = None):
    if not viewExists("artistsWithRandomCover"):
        indexArtistsWithRandomCover()

    return loadView("artistsWithRandomCover")


def getArtists(tracks):
    artists = []
    if tracks:
        for track in tracks:
            artist = track.artist
            if not artist in artists:
                artists.append(artist)
    return sorted(artists)


def getArtistsAlbums():
    result = loadView('artistsAlbums')
    return result

@profile
def getTracks():
    return load()


def getAlbum(albumTitle):
    tracksForAlbum = getTracksForAlbum(albumTitle)
    cover = ""
    for track in tracksForAlbum:
        if os.path.isfile(track.albumCoverPath):
            cover = track.albumCoverPath
            break

    return {'album': albumTitle, 'artist':tracksForAlbum[0].artist, 'albumCoverPath': cover}

def getTracksForAlbum(albumTitle, artistName = None, _tracks = None):
    if not viewExists("albums"):
        indexAlbums()
    albums = loadView("albums")
    print albums[albumTitle]
    return albums[albumTitle]

def indexAlbums():
    tracks = load()
    albums = {}
    if tracks:
        for track in tracks:
            if not track.albumTitle in albums:
                albums[track.albumTitle] = []    
            
            albums[track.albumTitle].append(track)
    saveView("albums", albums)
    
def save(tracks):
    print "Saving tracks to file..."
    print config.getConfigFolder() + 'artists.mc'
    try:
        with open(config.getConfigFolder() + 'artists.mc', 'wb') as _file:
            json.dump(tracks, _file)
            return True
    except IOError as e:
        logging.debug(e)
        print e
    return False

def load():
    try:
        indexLocation = config.getConfigFolder() + 'artists.mc'
        with open(indexLocation, 'rb') as _file:
            tracks = json.load(_file)
            return tracks
    except IOError as e:
        logging.debug(e)
        print e
    return None

def saveView(viewName, data):
    print "Saving view to file..."
    viewFileName = config.getConfigFolder() + viewName + ".mc"
    print viewFileName
    try:
        with open(viewFileName, 'wb') as _file:
            json.dump( data, _file)
            return True
    except IOError as e:
        logging.debug(e)
        print e
    return False


def loadView(viewName):
    if viewName in VIEWS:
        print "Loading view from memory: {0}".format(viewName)
        return VIEWS[viewName]

    print "Loading view from file: {0}".format(viewName)
    try:
        indexLocation = config.getConfigFolder() + viewName + ".mc"
        print indexLocation
        with open(indexLocation, 'rb') as _file:
            viewData = json.load(_file)
            VIEWS[viewName] = viewData
            return viewData
    except IOError as e:
        logging.debug(e)
        print e
    return None

def viewExists(viewName):
    viewPath = config.getConfigFolder() + viewName + ".mc"
    print "Check if view exists by looking at the file: ", viewPath
    try:
        with open(viewPath) as f:
            print "The view file was found. ", f
            return True
    except IOError as e:
        print "The view file could not be found: ", e
        return False
        

def indexArtistsWithRandomCover():
    tracks = load()
    artists = []
    artists_names = []

    if tracks:
        for track in tracks:
            artist = track.artist
            if not artist in artists_names:
                if track.albumCoverPath:
                    artists_names.append(artist)
                    artists.append([artist, track.albumCoverPath])

        for track in tracks:
            artist = track.artist
            if not artist in artists_names:
                artists_names.append(artist)
                artists.append([artist, '../art/nocover1.jpg'])
    data = sorted(artists, key=lambda x: x[0])
    saveView("artistsWithRandomCover", data)


class LibraryIndexationTask(QtCore.QThread):
     def __init__(self, pathToIndex = None, parent=None):
         QThread.__init__(self, parent)
         self.exiting = False
         self.pathToIndex = pathToIndex
         print "Creating new indexation task for folder: ", self.pathToIndex

     def run(self):
        reIndex(self.pathToIndex, self.progressCallback)

     def getWorkload(self):
        from indexation import MusicIndexer
        return MusicIndexer(self.pathToIndex).getNumberOfFilesToHandle()

     def progressCallback(self, i):
        self.emit(SIGNAL("progress(int)"), i)

@profile
def reIndex(pathToIndex = None, progressCallback = None):
    from indexation import MusicIndexer
    tracks, report = MusicIndexer(pathToIndex, progressCallback).run()
    save(tracks)

    indexAlbums()
    indexArtistsWithRandomCover()
   

def extractArtwork():
    config.setConfigFolder('../config/')
    tracks = load()
    from mutagen import File
    from mutagen.flac import FLAC
    import os

    for track in tracks:
        print track
        dirname = os.path.dirname(track.filePath)
        coverFullname = dirname + "/" + "cover.jpg"

        _file = File(track.filePath) # mutagen can automatically detect format and type of tags
        artwork = None
        try:
            artwork = _file.tags['APIC:'].data # access APIC frame and grab the image
        except KeyError as e:
            pass
        if not artwork:
            try:
                if track.filePath.endswith(".flac"):
                    _file = FLAC(track.filePath)
                    if len(_file.pictures) > 0:
                        artwork = _file.pictures[0].data
            except KeyError as e:
                pass
        if artwork:
            if not os.path.isfile(coverFullname):
                print "will write {0}".format(coverFullname)
                with open(coverFullname, 'wb') as f:
                    f.write(artwork) # write artwork to new image    

if __name__ == '__main__':
    import config
    config.setConfigFolder('../config/')
    indexArtistsWithRandomCover()
    indexAlbums()
