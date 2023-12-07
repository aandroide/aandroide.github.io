import xbmc
import xbmcaddon
import logging
from resources.modules.player_overlay import OverlayText

logger = logging.getLogger(xbmcaddon.Addon().getAddonInfo('id'))


class TheGroovePlayer(xbmc.Player):
    def __init__(self, *args, **kwargs):
        self.is_active = True
        self.ace_api = None
        self.overlay = OverlayText()
        xbmc.Player.__init__(self)
        logger.debug("THEGROOVE PLAYER")

    def onPlayBackPaused(self):
        logger.debug("#Im paused#")

    def onPlayBackResumed(self):
        logger.debug("#Im Resumed #")

    def onPlayBackStarted(self):
        logger.debug("#Playback Started#")
        # xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
        try:
            logger.debug("#Im playing :: " + self.getPlayingFile())
        except:
            logger.debug("#I failed get what Im playing#")

    def onAVStarted(self):
        logger.debug("#Audio Video Started#")
        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
        try:
            self.ace_api.pb_dialog.close()
        except:
            pass

    def onPlayBackEnded(self):
        logger.debug("#Playback Ended#")
        self.is_active = False

    def onPlayBackStopped(self):
        logger.debug("## Playback Stopped ##")
        self.is_active = False
        self.ace_api.stop_player()
        self.overlay.close()

    def sleep(self, s):
        xbmc.sleep(s)

    def set_ace_api(self, ace_api):
        self.ace_api = ace_api

