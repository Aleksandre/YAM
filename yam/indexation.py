
"""
This module contains music indexation logic.
"""
import os
from profiling import profile
from mutagen import mutagen
from content import Track
import os.path
import time
import logging
import config
import cPickle as json

class MusicIndexer:
    """
    This class will scan a folder recursievely looking for music files.

    Each file tags are extracted using mutagen.

    Each time a track is read, the progressCallback method is called
    """

    def __init__(self, pathToIndex = None, progressCallback = None):
        self.pathToIndex = pathToIndex or config.getProperty('music_library_folder')
        self.progressCallback = progressCallback
        self.supported_audio_extensions = [".mp3", ".flac"]
        self.supported_cover_extensions = [".png", ".bmp", ".jpeg", ".jpg"]
        self.likely_artcover_name = ["front", "cover", "art", "folder", "album", ".front", ".cover", ".art", ".folder", ".album"]

    @profile
    def run(self):
        print "Starting indexation of folder: ", self.pathToIndex
        startTime = time.time()
        result = Result()
        #Scan configured directory for all music files
        musicFiles = []
        rootdir = self.pathToIndex
        for root, subFolders, files in os.walk(rootdir):
            for file in files:
                filename, ext = os.path.splitext(file)
                if ext in self.supported_audio_extensions:
                    musicFiles.append(os.path.join(root,file))

        #Try to extract audio metadata from files
        i = 0
        tracks = []
        unhandled_files = []
        result.totalFileCount = len(musicFiles)
        for audioFile in musicFiles:
            try:
                metadata = mutagen.File(audioFile.strip(), easy=True)
                if metadata :
                    track = self._indexTrack(metadata, audioFile)
                    if track:
                        result.numberOfIndexedFiles +=1;
                        tracks.append(track)
                    else :
                        unhandled_files.append(audioFile)
                else :
                    unhandled_files.append(audioFile)
            except Exception as e:
                print e
                unhandled_files.append(audioFile)

            i = i + 1
            if self.progressCallback:
                self.progressCallback(i)

        result.numberOfFilesNotImported = len(unhandled_files)
        result.filesNotImported = unhandled_files
        result.processRunningTimeInMS = (time.time() - startTime)
        self._saveResult(result)
        self.progressCallback(result.totalFileCount)
        return tracks, result


    def getNumberOfFilesToHandle(self):
        """Scan the configured path to get how many files will be handled
        when the indexer is actually ran with the current configuration.
        """
        count = 0
        rootdir = self.pathToIndex
        for root, subFolders, files in os.walk(rootdir):
            for file in files:
                filename, ext = os.path.splitext(file)
                if ext in self.supported_audio_extensions:
                    count = count + 1
        print "The music indexer will try to index ", str(count), " file(s)."
        return count

    def resetArt(self, tracks):
        for track in tracks:
            track.albumCoverPath = ""
        return tracks

    def _indexTrack(self, trackData, track_path):
        track = Track()
        try:
            if "title" in trackData: track.title = trackData["title"][0].title() or 'No Title({0})'.format(row + 1)
            if "artist" in trackData: track.artist = trackData["artist"][0].title() or 'Unknown Artist'
            if "album" in trackData: track.albumTitle = trackData["album"][0].title() or 'Unknown {0} Album'.format(track.artist)
            track.lengthMS = trackData.info.length
            if "tracknumber" in trackData:
                trackNum = trackData["tracknumber"][0]
                track.num = trackNum
            track.filePath = track_path
            track.albumCoverPath = self._getAlbumCover(os.path.dirname(track.filePath))
        except Exception as e:
            print e
            return track
        return track

    def _getAlbumCover(self, albumRootDir):
        coverPath = ""
        #For each file found in album folder
        for _file in os.listdir(albumRootDir):
            #Don't recurse. If it's a dir, skip to next file.
            if os.path.isdir(_file):
                continue
            filename, ext = os.path.splitext(_file)

            #Is the file an image ?
            if ext.lower() in self.supported_cover_extensions:
                #It is

                coverPath = os.path.join(albumRootDir , _file)
                #print coverPath
                #Is the file name make it likely to be the cover ?
                if filename.lower() in self.likely_artcover_name:
                    #Yes, my work is done, perfect match, get out.
                    break
                else:
                    #The name is weird, keep it anyway in case no other
                    #image is found.
                    coverPath = os.path.join(albumRootDir,ext)

        return coverPath

    def _saveResult(self, result):
        reportFolder = config.getFullFileName("reports/")
        from datetime import datetime
        now = datetime.now()
        resultFilename = reportFolder + "{0}.txt".format(datetime(now.year, now.month, now.day, now.hour, now.minute))
        try:
            if not os.path.exists(reportFolder):
                os.makedirs(reportFolder)
        except IOError as e:
            print "Could not create directory to save results: {0}".format(reportFolder)
            return False

        print "Saving indexation result..."
        try:
            with open(resultFilename, 'wb') as f:
                json.dump(result, f)
                return True
        except IOError as e:
            logging.debug(e)
            print e
            return False

class Result:
    totalFileCount = 0
    numberOfIndexedFiles = 0
    numberOfFilesNotImported = 0
    processRunningTimeInMS = 0
    trackIndexFilename = ""
    filesNotImported = []

    def __init__(self):
        pass

@profile
def reIndexArt():
    import content, config
    config.setConfigFolder('../config/')
    indexer = MusicIndexer()
    tracks = content.load()
    for track in tracks:
        track.albumCoverPath = indexer._getAlbumCover(os.path.dirname(track.filePath)).encode("utf-8")
    content.save(tracks)


def reIndex():
    reIndexArt()

if __name__ == '__main__':
    reIndexArt()