
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

#Whenever a view is read, it is stored in in VIEWS dictionnary.
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
def indexAlbums():
    tracks = getTracks()
    albums = {}
    if tracks:
        for track in tracks:
            if not track.albumTitle in albums:
                albums[track.albumTitle] = []

            albums[track.albumTitle].append(track)
    saveView("albums", albums)

@profile
def indexArtistsWithRandomCover():
    tracks = getTracks()
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


@profile
def getAlbums(_tracks = None):
    """
    Returns distinct album names from the specified tracks.

    Tracks is expected to be an [] of Track

    Result example: [albumTitle1, albumTitle2, ...]
    """
    tracks = _tracks or getTracks()
    albums = []

    if tracks:
        for track in tracks:
            album = track.albumTitle
            if not album in albums:
                albums.append(album)
    return sorted(albums)

@profile
def getArtistsWithRandomCover():
    """
    Returns a list of all artists with a cover choosed randomly among the artist albums.

    Result example : [ {artist1, art/cover1.png}, {artist2, art/cover2.png}, ...]
    """
    if not viewExists("artistsWithRandomCover"):
        indexArtistsWithRandomCover()

    return loadView("artistsWithRandomCover")

@profile
def getArtists(tracks):
    """
    Returns distinct artists names from the specified tracks.

    The names are sorted alphabetically.

    Tracks is expected to be an [] of Track

    Result example: [artistName1, artistName2, ...]
    """
    artists = []
    if tracks:
        for track in tracks:
            artist = track.artist
            if not artist in artists:
                artists.append(artist)
    return sorted(artists)

@profile
def getArtistsAlbums():
    """
    Return a list of every album with full Track object.

    Result example: { {albumTitle: [Track1, Track2, ...]}, {title2, Tracks2[]},... }
    """
    if not viewExists("albums"):
        indexAlbums()
    return loadView('albums')

@profile
def getTracks():
    """
    Return a list of Track objects.

    Result example : [Track1, Track2, ...]
    """
    return loadView('tracks')

@profile
def getAlbum(albumTitle):
    """
    Return the artist name and album cover path for the specified album.

    As an example, if albumTile=18,
    the result will be: {'album': 18, 'artist':Moby, 'albumCoverPath': cover.png}
    """
    tracksForAlbum = getTracksForAlbum(albumTitle)
    cover = ""
    artistName = ""
    if tracksForAlbum and len(tracksForAlbum > 0):
        cover = tracksForAlbum[0].albumCoverPath
        artistName = tracksForAlbum[0].artist

    return {'album': albumTitle, 'artist':artistName, 'albumCoverPath': cover}

@profile
def getTracksForAlbum(albumTitle, artistName = None, _tracks = None):
    if not viewExists("albums"):
        indexAlbums()
    albums = loadView("albums")
    return albums[albumTitle]

def saveView(viewName, data):
    workspace = config.getWorkspaceLocation()
    viewFileName = workspace + "/" + viewName + ".mc"
    print "Saving view '{0}'into workspce: {1}".format(viewName, workspace)
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
        indexLocation = config.getFullFileName(viewName + ".mc")
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
    viewPath = config.getFullFileName(viewName + ".mc")
    print "Checking if view exists by looking at the file: ", viewPath
    try:
        with open(viewPath) as f:
            print "The view file was found. ", f
            return True
    except IOError as e:
        print "The view file could not be found: ", e
        return False


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
    global VIEWS
    VIEWS.clear()

    tracks, report = MusicIndexer(pathToIndex, progressCallback).run()
    saveView('tracks', tracks)

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
