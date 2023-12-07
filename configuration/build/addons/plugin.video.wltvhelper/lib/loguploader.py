import os
import re
import socket
import requests
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

from lib import utils, config, logger

ADDONID = config.ADDON_ID
ADDONNAME = config.ADDON_NAME
ADDONVERSION = config.ADDON_VERSION
ADDONPATH = config.ADDON_PATH

socket.setdefaulttimeout(5)

URL = 'https://paste.kodi.tv/'
LOGPATH = xbmcvfs.translatePath('special://logpath')
LOGFILE = os.path.join(LOGPATH, 'kodi.log')
REPLACES = (('//.+?:.+?@', '//USER:PASSWORD@'),('<user>.+?</user>', '<user>USER</user>'),('<pass>.+?</pass>', '<pass>PASSWORD</pass>'),)


def log(txt):
    logger.debug(txt)


class LogView(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.name = kwargs["name"]
        self.content = kwargs["content"]

    def onInit(self):
        self.header = 501
        self.textbox = 502
        self.showdialog()

    def showdialog(self):
        self.getControl(self.header).setLabel(self.name)
        self.getControl(self.textbox).setText(self.content)
        self.setFocusId(503)


class Main():
    def __init__(self, customReplacesList: list):
        log("log uploader script started")
        files = self.getFiles()
        for item in files:
            filetype = item[0]
            if filetype == "log":
                error = config.getString(30172)
                name  = config.getString(30173)
            succes, data = self.readLog(item[1])
            if succes:
                content = self.cleanLog(data, customReplacesList)
                dialog = xbmcgui.Dialog()
                confirm = dialog.yesno(ADDONNAME, config.getString(30174) % name, nolabel=config.getString(30175), yeslabel=config.getString(30176))
                if confirm:
                    succes, data = self.postLog(content)
                    if succes:
                        self.showResult(config.getString(30170) % (name, data), data)
                    else:
                        self.showResult('%s[CR]%s' % (error, data))
                else:
                    lv = LogView("script-loguploader-view.xml", ADDONPATH, "Default", name=name, content=content)
                    lv.doModal()
                    del lv
            else:
                self.showResult('%s[CR]%s' % (error, data))
        log('log uploader script ended')

    def getFiles(self):
        logfiles = []
        logfiles.append(['log', LOGFILE])
        return logfiles

    def readLog(self, path):
        try:
            lf = xbmcvfs.File(path)
            sz = lf.size()
            if sz > 2000000:
                log('file is too large')
                return False, config.getString(30169)
            content = lf.read()
            lf.close()
            if content:
                return True, content
            else:
                log('file is empty')
                return False, config.getString(30166)
        except:
            log('unable to read file')
            return False, config.getString(30167)

    def cleanLog(self, content, customReplacesList: list):
        for pattern, repl in REPLACES:
            content = re.sub(pattern, repl, content)

        if customReplacesList:
            for pattern in customReplacesList:
                content = re.sub(pattern, "******************************", content)

        return content

    def postLog(self, data):
        self.session = requests.Session()
        UserAgent = "script.kodi.loguploader: 1.0.4"
        try:
            response = self.session.post(URL + 'documents', data=data.encode('utf-8'), headers={'User-Agent': UserAgent})
            if 'key' in response.json():
                result = URL + response.json()['key']
                return True, result
            elif 'message' in response.json():
                log('upload failed, paste may be too large')
                return False, response.json()['message']
            else:
                log('error: %s' % response.text)
                return False, config.getString(30171)
        except:
            log('unable to retrieve the paste url')
            return False, config.getString(30168)

    def showResult(self, message, url=None):
        dialog = xbmcgui.Dialog()
        dialog.ok(ADDONNAME, message)
