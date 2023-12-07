import xbmcgui
import xbmc
import xbmcaddon
import xbmcvfs
import os
import sys

if sys.version_info[0] > 2:
    addonpath = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('Path'))
else:
    addonpath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('Path'))


class OverlayText(object):
    def __init__(self):
        self.showing = False
        self.window = xbmcgui.Window(12005)
        viewport_w, viewport_h = self._get_skin_resolution()
        font_max = 'font13'
        font_min = 'font10'
        origin_x = int(float(viewport_w) / 1.3913)
        origin_y = int(float(viewport_h) / 8.0)
        window_w = int(float(viewport_w) / 3.7647)
        window_h = int(float(viewport_h) / 2.5714)
        acelogo_w = int(float(window_w) / 8.5)
        acelogo_h = int(float(window_w) / 11.0)
        text_lat = int(float(window_w) / 15)
        text_w = int(float(window_w) / 1.7)
        text_h = int(float(window_h) / 14)
        fst_setting = int(float(window_h) / 3.5)
        fst_stat_setting = int(float(window_h) / 1.4)

        # main window
        self._background = xbmcgui.ControlImage(origin_x, origin_y, window_w, window_h,
                                                os.path.join(addonpath, "resources", "images", "background.png"))
        self._acestreamlogo = xbmcgui.ControlImage(origin_x + int(float(window_w) / 11.3),
                                                   origin_y + int(float(window_h) / 14), acelogo_w, acelogo_h,
                                                   os.path.join(addonpath, "resources", "images", "acelogo.png"))
        self._supseparator = xbmcgui.ControlImage(origin_x, origin_y + int(float(viewport_h) / 12.176), window_w - 10,
                                                  1, os.path.join(addonpath, "resources", "images", "separator.png"))
        self._botseparator = xbmcgui.ControlImage(origin_x, origin_y + window_h - 30, window_w - 10, 1,
                                                  os.path.join(addonpath, "resources", "images", "separator.png"))
        self._title = xbmcgui.ControlLabel(origin_x + int(float(window_w) / 3.4), origin_y + text_h, window_w - 140,
                                           text_h, "AceStream Engine", font=font_max, textColor='0xFFEB9E17')
        self._total_stats_label = xbmcgui.ControlLabel(origin_x + int(float(window_h) / 1.72),
                                                       origin_y + int(float(window_h) / 1.6),
                                                       int(float(window_w) / 1.7), 20, "Stats", font=font_min,
                                                       textColor='0xFFEB9E17')
        # labels
        self._action = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_setting, int(float(text_w) * 1.6),
                                            text_h, "Status:" + ' N/A', font=font_min)
        self._download = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_setting + text_h,
                                              int(float(text_w) * 1.6), text_h, "Download:" + ' N/A', font=font_min)
        self._upload = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_setting + 2 * text_h, text_w, text_h,
                                            "Upload:" + ' N/A', font=font_min)
        self._seeds = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_setting + 3 * text_h, text_w, text_h,
                                           "Peers:" + ' N/A', font=font_min)
        self._total_download = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_stat_setting, text_w, text_h,
                                                    "Downloaded:" + ' N/A', font=font_min)
        self._total_upload = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_stat_setting + text_h, text_w,
                                                  text_h, "Uploaded" + ' N/A', font=font_min)
        self._percent_value = xbmcgui.ControlLabel(origin_x + int(float(window_h) / 1.25), origin_y + fst_setting,
                                                   text_w, text_h, 'N/A', font=font_min)

        self.window.addControl(self._background)
        self.window.addControl(self._acestreamlogo)
        self.window.addControl(self._supseparator)
        self.window.addControl(self._botseparator)
        self.window.addControl(self._title)
        self.window.addControl(self._action)
        self.window.addControl(self._download)
        self.window.addControl(self._upload)
        self.window.addControl(self._seeds)
        self.window.addControl(self._total_stats_label)
        self.window.addControl(self._total_download)
        self.window.addControl(self._total_upload)
        self.window.addControl(self._percent_value)

        self.hide()

    def show(self):
        try:
            self.showing = True

            self._background.setVisible(True)
            self._acestreamlogo.setVisible(True)
            self._supseparator.setVisible(True)
            self._botseparator.setVisible(True)
            self._title.setVisible(True)
            self._action.setVisible(True)
            self._download.setVisible(True)
            self._upload.setVisible(True)
            self._seeds.setVisible(True)
            self._total_stats_label.setVisible(True)
            self._total_download.setVisible(True)
            self._total_upload.setVisible(True)
            self._percent_value.setVisible(True)

        except:
            pass

    def hide(self):
        self.showing = False

        self._background.setVisible(False)
        self._acestreamlogo.setVisible(False)
        self._supseparator.setVisible(False)
        self._botseparator.setVisible(False)
        self._title.setVisible(False)
        self._action.setVisible(False)
        self._download.setVisible(False)
        self._upload.setVisible(False)
        self._seeds.setVisible(False)
        self._total_stats_label.setVisible(False)
        self._total_download.setVisible(False)
        self._total_upload.setVisible(False)
        self._percent_value.setVisible(False)

    def set_information(self, engine_data):
        if self.showing:
            status = engine_data["status"]
            dkbs = str(engine_data["speed_down"]) + "Kb/s"
            ukbs = str(engine_data["speed_up"]) + "Kb/s"
            ded = float(engine_data["downloaded"])
            ued = engine_data["uploaded"]
            t_prog = engine_data["total_progress"]
            peers = engine_data["peers"]

            ded_mb = str(round(float(ded) / (2 ** 20), 2))
            ued_mb = str(round(float(ued) / (2 ** 20), 2))

            self._action.setLabel("Status:" + ' ' + status)
            self._download.setLabel("Download:" + '  ' + dkbs)
            self._upload.setLabel("Upload" + ' ' + ukbs)
            self._seeds.setLabel("Peers:" + ' ' + str(peers))
            self._total_download.setLabel("Downloaded:" + ' ' + str(ded_mb) + " MB")
            self._total_upload.setLabel("Uploaded:" + ' ' + str(ued_mb) + " MB")
            self._percent_value.setLabel(str(t_prog) + "%")
        else:
            pass

    def close(self):
        if self.showing:
            self.hide()

        try:
            self.window.clearProperties()
        except:
            pass

    # Taken from xbmctorrent
    @staticmethod
    def _get_skin_resolution():
        import xml.etree.ElementTree as ET
        if sys.version_info[0] > 2:
            skin_path = xbmcvfs.translatePath("special://skin/")
        else:
            skin_path = xbmc.translatePath("special://skin/")
        tree = ET.parse(os.path.join(skin_path, "addon.xml"))
        try:
            res = tree.findall("./res")[0]
        except:
            res = tree.findall("./extension/res")[0]
        return int(res.attrib["width"]), int(res.attrib["height"])
