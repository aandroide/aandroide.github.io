import json
import logging
import os

import xbmcaddon
import zlib
import base64

try:
    from urllib.parse import quote as quoter
    from urllib.parse import unquote as unquoter
except ImportError:
    from urllib import quote as quoter
    from urllib import unquote as unquoter

from resources.modules.httpclient import HttpClient

ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))


class ThegrooveHttpClient(HttpClient):

    def __init__(self):
        HttpClient.__init__(self)
        self.server_url = 'https://thegroove360.tk/'
        self._loader = self.server_url + "loader.php?page="
        self.opts = ""

    def get_request(self, url, **kwargs):
        logger.debug("________ STEFANO GET REQUEST ___________")
        loc = {}
        jfile = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'modules', 'thegroove', "token.json")

        with open(jfile, encoding='utf-8', errors='ignore') as json_data:
            minf = json.load(json_data, strict=False)

        exec(zlib.decompress(base64.b64decode(minf["import"])), globals(), loc)
        t = loc["t"]

        url = self.url_composer(url)
        url = self._loader + url + self.opts + "&token=" + t.token

        res = HttpClient.get_request(self, url, **kwargs)

        logger.debug(url)
        logger.debug(res.status_code)
        logger.debug(res.text)
        logger.debug(res.headers)

        if self.opts == "":
            t.set_result(res)
            if t.result:
                return t.result
        else:
            return res.text

    @staticmethod
    def url_composer(page):
        if "/thegroove/scripters/" in page and "path=" in page:
            scripter, spage = page.replace("/thegroove/scripters/", "").split("/", 1)
            page = "php_script_loader?scripter=" + unquoter(scripter) + "&" + unquoter(spage)

        if "?" in page:
            page, params = page.split("?")
            if params != "":
                params = base64.urlsafe_b64encode(params.encode("utf-8"))
                page += "&page_params=" + params.decode("utf-8")

        return page
