# -*- coding: utf-8 -*-

import xbmcaddon, sys, os
import xbmcvfs
from xbmcvfs import translatePath

ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo("name") 
ADDON_ID   = ADDON.getAddonInfo("id")
ADDON_PATH = ADDON.getAddonInfo("path")
ADDON_USER_PATH = ADDON.getAddonInfo("profile")
ADDON_VERSION   = ADDON.getAddonInfo("version")
ADDON_ROOT_PATH = translatePath("special://home/addons/")


def cleaunUpSettings():
    if getSetting("personal_list"):
        setSetting("personal_list", "")
    if getSetting("user_list"):
        setSetting("user_list", "")


def getSetting(name):
    value = ADDON.getSetting(name)
    if value == "true":
        value = True
    elif value == "false":
        value = False
    else:
        try:
            value = int(value)
        except ValueError:
            pass
    return value


def setSetting(name, value):
    if value == True:
        value = "true"
    elif value == False:
        value = "false"
    else:
        value = str(value)
    ADDON.setSetting(name, value)


def openSettings():
    ADDON.openSettings()


def getAddonInfo(name):
    return ADDON.getAddonInfo(name)


def quality(qualities):
    resolutions = [1080, 720, 480]
    resolution = resolutions[int(getSetting("resolutions"))]
    selected = [min(range(len(qualities)), key=lambda i: abs(int(qualities[i]) - resolution))][0]
    return selected


def getString(ID):
    return ADDON.getLocalizedString(ID)


def isDEV():
    return os.path.isdir(os.path.join(ADDON_PATH, ".git"))


def isBeta():
    return "~beta" in ADDON_VERSION or "~rc" in ADDON_VERSION 