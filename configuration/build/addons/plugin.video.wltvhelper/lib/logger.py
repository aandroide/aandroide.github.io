# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Logger (kodi)
# --------------------------------------------------------------------------------
import inspect, os, xbmc, sys
from lib import config
from lib.config import getSetting

APP_NAME = config.getString(30000)

try:
    xbmc.KodiStub()
    testMode = True
    record = False
    recordedLog = ""
    import html
except:
    testMode = False

LOG_FORMAT = "{addname}[{filename}.{function}:{line}]{sep} {message}"
DEBUG_ENABLED = getSetting("debug") or config.isDEV()
DEF_LEVEL = xbmc.LOGINFO


def info(*args):
    log(*args)


def debug(*args):
    if DEBUG_ENABLED:
        log(*args)


def error(*args):
    log("######## ERROR #########", level=xbmc.LOGERROR)
    log(*args, level=xbmc.LOGERROR)


def log(*args, **kwargs):
    msg = ""
    
    for arg in args:
        msg += " " + str(arg)

    if testMode and record:
        global recordedLog
        recordedLog += msg + "\n"
        return
    
    frame = inspect.currentframe().f_back.f_back
    filename = frame.f_code.co_filename
    filename = os.path.basename(filename).split(".")[0]
    xbmc.log(
        LOG_FORMAT.format(
            addname=APP_NAME,
            filename=filename,
            line=frame.f_lineno,
            sep=":" if msg else "",
            function=frame.f_code.co_name,
            message=msg,
        ),
        kwargs.get("level", DEF_LEVEL),
    )


class WebErrorException(Exception):
    def __init__(self, url, channel, *args, **kwargs):
        self.url = url
        self.channel = channel
        Exception.__init__(self, *args, **kwargs)


class ChannelScraperException(Exception):
    pass

#  Debugger
def dbg(open_web_browser=False):
    if config.isDEV():
        from lib.install import installWebPdb

        addon = installWebPdb()
        if addon:
            sys.path.append(addon[0])
            sys.path.append(addon[1])
            try:
                import web_pdb

                if not web_pdb.WebPdb.active_instance and open_web_browser:
                    import webbrowser

                    webbrowser.open("http://127.0.0.1:5555")
                web_pdb.set_trace()
            except:
                pass
