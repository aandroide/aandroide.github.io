# -*- coding: utf-8 -*-

import requests
from lib import scrapers, config, utils, logger
from lib.broadcaster_result import BroadcasterResult

HOST = "https://supertennis.tv/"

headers = {
    "User-Agent": utils.USER_AGENT,
    "Referer": HOST,
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Dest": "iframe",
}

mpd = config.getSetting("mpd")


def play(search):
    res = BroadcasterResult()

    url = ""
    streamType = "mdp" if mpd else "m3u8"

    data = requests.get(f"{HOST}Areas/Supertennis/Scripts/live-streaming.js").text
    url = scrapers.findSingleMatch(data, r'clearInterval.*?iframe.*?manifest_url=([^&]+)')

    if url:
        url = "{}|user-agent={}".format(url, utils.USER_AGENT)

        res.ManifestType = "hls"
        url = f"{url}|user-agent={utils.USER_AGENT}" #kodi 19 compatibility
        res.StreamHeaders = f"user-agent={utils.USER_AGENT}"
        res.Url = url

    return res
