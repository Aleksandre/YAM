import sys, os

from ConfigParser import SafeConfigParser


class Properties:
    MUSIC_LIBRARY="music_library_folder"


def setConfigFolder(newConfigLocation):
    coreParser = SafeConfigParser()
    coreParser.read("config.ini") 
    if not newConfigLocation.endswith("/") and not newConfigLocation.endswith("\\"):
        newConfigLocation = newConfigLocation + "/"
    coreParser.set('configuration', 'work_folder', newConfigLocation)

    with open("config.ini", 'w') as configfile:
        coreParser.write(configfile)


def getConfigFolder():
    config = "config.ini"
    coreParser = SafeConfigParser()
    coreParser.read(config) 

    configFolderPath = coreParser.get('configuration', 'work_folder')
    print "Reading config folder path: ", configFolderPath
    return configFolderPath

def getPathToMusicLibrary():
    parser = SafeConfigParser()
    print getConfigFolder() , '/appconfig.ini'
    parser.read(getConfigFolder() + '/appconfig.ini')
    return parser.get('global', 'music_library_folder')


def getIndexReportFolder():
    parser = SafeConfigParser()
    parser.read(getConfigFolder() + '/appconfig.ini')
    return parser.get('global', 'index_report_folder')


def getProperty(key):
    parser = SafeConfigParser()
    parser.read(getConfigFolder() + 'appconfig.ini')
    print parser.get('global', key)

def setProperty(key, value):
    print "Setting property[", key, "=", value, "]"
    parser = SafeConfigParser()
    parser.read(getConfigFolder() + 'appconfig.ini')
    parser.set('global', key, value)
    with open(getConfigFolder() + 'appconfig.ini', 'w') as configfile:
        print parser.write(configfile)

if __name__ == '__main__':
    print getConfigFolder()