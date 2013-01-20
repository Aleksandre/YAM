

"""
This module contains everything related to the app configuration
"""
from ConfigParser import SafeConfigParser
import os, sys

_CONFIG_FOLDER = None

class Properties:
    MUSIC_LIBRARY="music_library_folder"

def setConfigFolder(newConfigLocation):
    global _CONFIG_FOLDER
    _CONFIG_FOLDER = newConfigLocation

def getConfigFolder():
    return _CONFIG_FOLDER

def createConfigFile():
    try: 
        if os.path.isfile(getConfigFolder() + 'appconfig.ini'):
            return

        with open(getConfigFolder() + 'appconfig.ini', 'w+') as f:
            print f
            return True
    except Exception as e:
            print e
            print "here"
            return False

def deleteConfigFile():
    try:
        os.remove(_CONFIG_FOLDER + 'appconfig.ini')
        return True
    except Exception as e:
        print e
       # print "here"
        return False

def getProperty(key):
    print "Reading property value..."
    createConfigFile()
    parser = SafeConfigParser()
    parser.read(_CONFIG_FOLDER + 'appconfig.ini')
    value = parser.get('global', key)
    print "Read value is: {0}".format(value)
    return value

def setProperty(key, value):
    createConfigFile()
    print "Setting property[", key, "=", value, "]"
    parser = SafeConfigParser()
    parser.read(_CONFIG_FOLDER + 'appconfig.ini')
    if not parser.has_section('global'):
        parser.add_section('global')
    
    parser.set('global', key, value)
    with open(_CONFIG_FOLDER + 'appconfig.ini', 'w') as configfile:
        parser.write(configfile)