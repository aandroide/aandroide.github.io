# -*- coding: utf-8 -*-

import requests, json
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult


def play(search):
    res = BroadcasterResult()
    url = ""

    api = f"https://www.dailymotion.com/player/metadata/video/{search}"

    jsonData = requests.get(api).json()

    streamList = jsonData["qualities"]["auto"]
    for item in streamList:
        if item["type"] == "application/x-mpegURL":
            url = item["url"]
            break

    if url:
        res.Url = url
        res.ManifestType = "hls"

    return res
