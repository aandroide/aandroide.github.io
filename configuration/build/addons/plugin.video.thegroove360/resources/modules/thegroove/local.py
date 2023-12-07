import xbmc
import xbmcaddon
import xbmcvfs
import os
import sys
import json
import logging
logger = logging.getLogger(xbmcaddon.Addon().getAddonInfo('id'))


class LocalItem:

    def __init__(self):
        if sys.version_info[0] > 2:
            self.data_path = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        else:
            self.data_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        self.local_file = os.path.join(self.data_path, "thegroove_local.json")
        self.json_data = []

        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

        if not os.path.exists(self.local_file):
            with open(self.local_file, 'a'):
                os.utime(self.local_file, None)

    def read_json(self):
        with open(self.local_file) as json_file:
            try:
                self.json_data = json.load(json_file)
            except ValueError:
                self.json_data = []

    def write_json(self):
        with open(self.local_file, 'w') as outfile:
            json.dump(self.json_data, outfile)

    @staticmethod
    def get_local_item_src(fsrc):
        import xbmcvfs
        if sys.version_info[0] > 2:
            fsrc = xbmcvfs.translatePath(fsrc)
        else:
            fsrc = xbmc.translatePath(fsrc)

        try:
            with open(fsrc) as xml_src:
                src = xml_src.read()
                xml_src.close()
                return src
        except:
            try:
                xml_src = xbmcvfs.File(fsrc)
                src = xml_src.read()
                xml_src.close()
                return src
            except:
                raise

    @staticmethod
    def get_context_options(ind):
        addon = xbmcaddon.Addon().getAddonInfo('id')
        return [
            ('Modifica', 'XBMC.RunPlugin(plugin://' + addon + '/local/edit/' + str(ind) + ')'),
            ('Rimuovi', 'XBMC.RunPlugin(plugin://' + addon + '/local/remove/' + str(ind) + ')')
        ]