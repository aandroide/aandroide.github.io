from resources.modules.httpclient import HttpClient
import re
import string
import sys


class PanelApi:

    def __init__(self, url, **kwargs):
        self.url = url
        self.api_url = self.url.replace("/get.php?", "/player_api.php?")
        self.__dict__.update(**kwargs)
        self.types = ["Live", "VOD", "Series"]

    def root(self):
        ret = []
        for st in self.types:
            ret.append((st, self.url))
        return ret

    def get_live_categories(self, ids_category=None):
        url = self.api_url + "&action=get_live_categories"
        req = HttpClient().get_request(url)
        res = req.json()

        ret = []
        for r in res:
            if ids_category and int(r["category_id"]) not in ids_category:
                continue

            cname = filter(lambda x: x in string.printable, r["category_name"])
            if sys.version_info[0] > 2:
                cname = ''.join(list(cname))

            ret.append((self.api_url + "&action=get_live_streams&category_id=" + r["category_id"], cname))

        return ret

    def get_live_category_channels(self, url="", category_id=""):
        if category_id != "":
            url = self.api_url + "&action=get_live_streams&category_id=" + category_id

        ret = []
        req = HttpClient().get_request(url)
        res = req.json()

        regex = r'(http.*?://.*?(?:(?::[\d]+)|)/).*?\?.*?username=([^&]+).*?password=([^&]+)'
        base_url, username, password = re.compile(regex, re.DOTALL).findall(url)[0]

        for r in res:
            cname = filter(lambda x: x in string.printable, r["name"])
            if sys.version_info[0] > 2:
                cname = ''.join(list(cname))
            rurl = base_url + "live/" + username + "/" + password + "/" + str(r["stream_id"]) + ".ts"
            ret.append((cname, rurl))

        return ret

    def get_vod_categories(self):
        url = self.api_url + "&action=get_vod_categories"
        req = HttpClient().get_request(url)
        res = req.json()

        ret = []
        for r in res:
            cname = filter(lambda x: x in string.printable, r["category_name"])
            if sys.version_info[0] > 2:
                cname = ''.join(list(cname))
            ret.append((self.api_url + "&action=get_vod_streams&category_id=" + r["category_id"], cname))

        return ret

    def get_vod_category_channels(self, url="", category_id=""):
        if category_id != "":
            url = self.api_url + "&action=get_vod_streams&category_id=" + category_id

        ret = []
        req = HttpClient().get_request(url)
        res = req.json()

        regex = r'(http.*?://.*?(?:(?::[\d]+)|)/).*?\?.*?username=([^&]+).*?password=([^&]+)'
        base_url, username, password = re.compile(regex, re.DOTALL).findall(url)[0]

        for r in res:
            rurl = base_url + "movie/" + username + "/" + password + "/" + str(r["stream_id"]) + "." + r[
                "container_extension"]
            cname = filter(lambda x: x in string.printable, r["name"])
            if sys.version_info[0] > 2:
                cname = ''.join(list(cname))
            ret.append((cname, rurl))

        return ret

    def get_series_categories(self):
        url = self.api_url + "&action=get_series_categories"
        req = HttpClient().get_request(url)
        res = req.json()

        ret = []
        for r in res:
            ret.append((self.api_url + "&action=get_series&category_id=" + r["category_id"], r["category_name"]))

        return ret

    def get_series_info(self, url="", category_id=""):
        if category_id != "":
            url = self.api_url + "&action=get_series&category_id=" + category_id

        ret = []
        req = HttpClient().get_request(url)
        res = req.json()

        for r in res:
            rurl = self.api_url + "&action=get_series_info&series_id=" + str(r["series_id"])
            cname = filter(lambda x: x in string.printable, r["name"])
            if sys.version_info[0] > 2:
                cname = ''.join(list(cname))
            ret.append((cname, rurl))

        return ret

    def get_series_episode(self, url="", series_id=""):
        if series_id != "":
            url = self.api_url + "&action=get_series_info&series_id=" + series_id

        ret = []
        req = HttpClient().get_request(url)
        res = req.json()

        regex = r'(http.*?://.*?(?:(?::[\d]+)|)/).*?\?.*?username=([^&]+).*?password=([^&]+)'
        base_url, username, password = re.compile(regex, re.DOTALL).findall(url)[0]

        if res and res["episodes"]:
            for lse in res["episodes"]:
                for r in res["episodes"][lse]:
                    rurl = base_url + "series/" + username + "/" + password + "/" + str(r["id"]) + "." + r[
                       "container_extension"]
                    ret.append((r["title"], rurl))

        return ret
