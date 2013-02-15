

"""
This module contains everything related to the app configuration
"""
from ConfigParser import SafeConfigParser
import ConfigParser
import os, sys

#Hold the workspace used by the application.
#Do not access from outside the config module.
ACTIVE_WORKSPACE = ""

class Properties:
    MUSIC_LIBRARY="music_library_folder"


def workspaceIsSet():
    """
    Return True if the ACTIVE_WORKSPACE is set or if a workspace
    is set in config.ini.
    """
    return len(getWorkspaceLocation()) > 0

def getWorkspaceLocation():
    """Return the value of ACTIVE_WORKSPACE
    if ACTIVE_WORKSPACE is not set, read the value from workspace_location.ini
    """
    global ACTIVE_WORKSPACE
    if ACTIVE_WORKSPACE == "":
        ACTIVE_WORKSPACE = readWorkspaceLocation()
    return ACTIVE_WORKSPACE

def setWorkspaceLocation(newLocation):
    """
    Set ACTIVE_CONFIG_FOLDER with newLocation
    """
    global ACTIVE_WORKSPACE
    ACTIVE_WORKSPACE = newLocation

def readWorkspaceLocation():
    """
    Read and return the saved ACTIVE_WORKSPACE from workspace_location.ini
    """
    configFileName = os.getcwd() + "/workspace_location.ini"
    try:
        print "Reading ACTIVE_WORKSPACE from {0}".format(configFileName)
        with open(configFileName, 'r') as f:
            workspace = f.readline()
            print "Workspace is {0}".format(workspace or 'Undefined')
            return workspace
    except Exception as e:
        print "Could not read the workspace location: {0}".format(e)
        return ""

def writeWorkspaceLocation(newLocation = None):
    """
    Write newLocation to workspace_location.ini.
    if newLocation is not specified, write ACTIVE_WORKSPACE to workspace_location.ini
    """
    global ACTIVE_WORKSPACE
    configFileName = os.getcwd() + "/workspace_location.ini"
    print "Writing ACTIVE_WORKSPACE to: {0}".format(configFileName)
    with open(configFileName, 'w+') as f:
        f.write(ACTIVE_WORKSPACE)

def createConfigFile():
    try:
        if os.path.isfile(getFullFileName('appconfig.ini')):
            return
        print "Creating config file..."
        with open(getFullFileName('appconfig.ini'), 'w+') as f:
            f.write("[global]")
            return True
    except Exception as e:
            print e
            print "Error creating config file."
            return False


def getFullFileName(fileName):
    return getWorkspaceLocation() + "/" + fileName

def deleteConfigFile():
    try:
        os.remove(getFullFileName('appconfig.ini'))
        return True
    except Exception as e:
        print e
       # print "here"
        return False

def getProperty(key):
    print "Reading property value..."
    createConfigFile()
    parser = SafeConfigParser()
    try:
        parser.read(getFullFileName('appconfig.ini'))
        value = parser.get('global', key)
        print "Read value is: {0}".format(value)
        return value
    except (ConfigParser.NoOptionError  ,ConfigParser.NoSectionError) as e:
        print e
        return ""

def setProperty(key, value):
    createConfigFile()
    print "Setting property[", key, "=", value, "]"
    parser = SafeConfigParser()
    parser.read(getFullFileName('appconfig.ini'))
    if not parser.has_section('global'):
        parser.add_section('global')

    parser.set('global', key, value)
    with open(getFullFileName('appconfig.ini'), 'w') as configfile:
        parser.write(configfile)