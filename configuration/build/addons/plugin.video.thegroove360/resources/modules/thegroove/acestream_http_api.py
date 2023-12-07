import xbmcaddon
import xbmcgui
import xbmc
import requests
import logging

from resources.lib import kodiutils

logger = logging.getLogger(xbmcaddon.Addon().getAddonInfo('id'))


class AcestreamHttpApi:

    def __init__(self, is_torrent=False):
        self.engine_address = kodiutils.get_setting("acestream_server")
        self.engine_port = kodiutils.get_setting_as_int("acestream_port")
        self.stat_url = ""
        self.cmd_url = ""
        self.playback_url = ""

        self.pb_dialog = xbmcgui.DialogProgress()

        self.loading = True

        hash_param = "id" # if is_torrent else "id"

        self.stream_url = "http://" + self.engine_address + ":" + str(
            self.engine_port) + "/ace/getstream?" + hash_param + "={0}"

    def get_stream_url(self, info_hash, retry=False):
        self.stream_url = self.stream_url.format(info_hash)
        logger.debug(self.stream_url)
        res = requests.get(self.stream_url + "&format=json")
        r = res.json()
        logger.debug(r)

        if int(res.status_code) > 399:
            return xbmcgui.Dialog().ok('[B]Thegroove360[/B][CR]Acestream Engine Non Avviato')

        if r["error"]:
            if not retry:
                self.stream_url = "http://" + self.engine_address + ":" + str(
                    self.engine_port) + "/ace/getstream?infohash={0}"
                return self.get_stream_url(info_hash, True)
            return xbmcgui.Dialog().ok('[B]Thegroove360[/B][CR]Acestream Error:', r["error"])

        if r["response"]:
            re = r["response"]
            self.stat_url = re["stat_url"]
            self.cmd_url = re["command_url"]
            self.playback_url = re["playback_url"]

            stats = self.get_stats()
            if stats:
                return stats
            else:
                return None

    def stop_player(self):
        logger.debug("STOP PLAYER")
        res = requests.get(self.cmd_url + "?method=stop")
        logger.debug(res.json())

    def get_stats(self):
        logger.debug("_____________ GET STATS _____________")
        '''status - playback session status:
                        prebuf - prebuffering
                        dl - playback
                    peers - number of connected peers
                    speed_down - download speed (Kbytes per sec)
                    speed_up - upload (Kbytes per sec)
                    downloaded - total downloaded (bytes)
                    uploaded - total uploaded (bytes)
                    total_progress - download ratio in percentage to media size, valid for VOD only, for live always 0'''
        res = requests.get(self.stat_url)
        r = res.json()

        logger.debug(r)

        return r

    def show_stats(self):
        logger.debug("_____________ SHOW STATS _____________")

        while True:

            if xbmc.getCondVisibility('Window.IsActive(busydialog)') == 1:
                xbmc.executebuiltin('Dialog.Close(busydialog)')

            if self.pb_dialog.iscanceled():
                self.stop_player()
                return None

            r = self.get_stats()

            if r["response"]:
                re = r["response"]
                logger.debug(re)
                status = re["status"]
                dkbs = str(re["speed_down"]) + "Kb/s"
                ukbs = str(re["speed_up"]) + "Kb/s"
                ded = float(re["downloaded"])
                ued = re["uploaded"]
                peers = re["peers"]

                if ded < (12 * (2 ** 20)):
                    prog = (ded * 100) / (12 * (2 ** 20))
                    ded_mb = str(round(float(ded) / (2 ** 20), 2))
                    ued_mb = str(round(float(ued) / (2 ** 20), 2))
                    self.pb_dialog.update(int(prog),
                                          "Stato: %s - Down:%s / Up:%s - Peers:%s" % (status, dkbs, ukbs, str(peers)) +
                                          "[CR]Downloaded: %sMB - Uploaded: %sMB" % (ded_mb, ued_mb))
                else:
                    self.pb_dialog.close()
                    break

            elif r["error"]:
                return None

            xbmc.sleep(1000)

        xbmc.sleep(100)
        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
        return re["status"]
