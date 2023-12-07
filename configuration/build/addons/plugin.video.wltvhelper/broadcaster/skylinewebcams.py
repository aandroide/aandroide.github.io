# -*- coding: utf-8 -*-
import requests

from lib import utils, scrapers, logger
from lib.broadcaster_result import BroadcasterResult

HOST = "www.skylinewebcams.com"
BASE_URL = "https://{}/it/webcam/".format(HOST)
BASE_URL_STREAMS = "https://hd-auth.skylinewebcams.com/"

headers = {
    "host": HOST,
    "user-agent": utils.USER_AGENT,
    "accept": "text/html,application/xhtml+xml,application/xml",
    "accept-language": "en,en-US;q=0.9,it;q=0.8",
    "origin": HOST,
    "referer": HOST,
}


def play(search):
    res = BroadcasterResult()
    url = ""

    siteUrl = f"{BASE_URL}{search}.html"

    data = requests.get(siteUrl, headers=headers).text

    url = scrapers.findSingleMatch(data, r"source:\'(.*m3u8.*?)\'")
    url = BASE_URL_STREAMS + url.replace("livee.", "live.")

    if not url:  # try to find YT channel
        idYt = scrapers.findSingleMatch(data, r"videoId:\'(.*?)\'")
        url = f"plugin://plugin.video.youtube/play/?video_id={idYt}"

    res.Url = url

    return res
