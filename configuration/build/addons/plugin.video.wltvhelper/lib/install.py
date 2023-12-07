# -*- coding: utf-8 -*-

import xbmcgui, xbmc, os, sys
from lib import logger, config, utils
from inputstreamhelper import Helper
from xbmcaddon import Addon

dialog = xbmcgui.Dialog()

ADDON_REPO = "repository.wltv"
ADDON_ID_PVR = "pvr.iptvsimple"
ADDON_ID_INPUTSTREAM  = "inputstream.adaptive"
ADDON_ID_WEBPDB = "script.module.web-pdb"
ADDON_ID_BOTTLE = "script.module.bottle"

def install():
    res = installInputStreamAdaptive()
    installWidevine()
    if res:
        utils.MessageNotification(config.getString(30121))

def isOfficiallyInstalled():
    return isAddonInstalled(ADDON_REPO)

def isUpdateEnabled():
    return isAddonUpdatesEnabled(config.ADDON_ID)

def isPvrSimpleInstalled():
    return isAddonInstalled(ADDON_ID_PVR)

def installPvr():
    return installAddon(ADDON_ID_PVR, "PVR Simple Client", True)

def getPvrSimpleVersion():
    return getAddonVersion(ADDON_ID_PVR)

def installInputStreamAdaptive():
    return installAddon(ADDON_ID_INPUTSTREAM)

def getInputStreamAdaptiveVersion():
    return getAddonVersion(ADDON_ID_INPUTSTREAM)

def installWidevine():
    if not Helper("mpd", drm="widevine").check_inputstream():
        Helper("mpd", drm="widevine").install_widevine()

def installWebPdb():
    res = None
    if installAddon(ADDON_ID_WEBPDB) and installAddon(ADDON_ID_BOTTLE):
        webpdb = Addon(ADDON_ID_WEBPDB)
        bottle = Addon(ADDON_ID_BOTTLE)
        res = config.translatePath(os.path.join(webpdb.getAddonInfo("Path"), "libs")), config.translatePath(os.path.join(bottle.getAddonInfo("Path"), "lib"))
    return res

def isAddonInstalled(addonId):
    return xbmc.getCondVisibility(f"System.HasAddon({addonId})")

def isAddonUpdatesEnabled(addonId):
    import sqlite3 as sqlite

    files = utils.getFiles("special://database", "Addons*.db")

    if len(files) > 1:
        logger.error("More Addons files db into directory!!!")

    dbfilePath = files[0]
    db = sqlite.connect(dbfilePath)
    rows = db.execute(f"SELECT updateRule FROM update_rules WHERE addonID = '{addonId}'")
    res = rows.fetchone()
    db.close()

    isEnabled = not (res and res[0] == 1)

    if not isEnabled:
        logger.error("Addon autoupdates is disabled!!!")

    return isEnabled

def installAddon(addonId, addonName="", askActivation=False):
    # Check if an addon is installed, if it doesn't, ask to install it.
    isInstalled = isAddonInstalled(addonId)
    isActive = False

    if(not isInstalled):
        logger.debug(f"{addonId} seems to be not installed")
        xbmc.executebuiltin(f"InstallAddon({addonId})", wait=True)
        isInstalled = isAddonInstalled(addonId)

    if isInstalled:
        try:
            # Check if it's active
            isActive = Addon(id=addonId) != None
        except:
            # if it's not active ask to activate it
            activate = True
            if askActivation:
                if not addonName:
                    addonName = addonId
                activate = utils.MessageBoxQuestion(config.getString(30111).format(addonName))
            if activate:
                xbmc.executeJSONRPC('{{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": {{ "addonid": "{}", "enabled": true }}}}'.format(addonId))
                isActive = Addon(id=addonId)

    return isInstalled and isActive

def getAddonVersion(addonId):
    addon = Addon(id=addonId)
    return addon.getAddonInfo("version")

