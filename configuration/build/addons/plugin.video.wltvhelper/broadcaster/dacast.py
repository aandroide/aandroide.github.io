# -*- coding: utf-8 -*-

import requests
from lib import scrapers, logger
from lib.broadcaster_result import BroadcasterResult


def play(search):
    res = BroadcasterResult()
    url = ""

    sSplit = search.split("$")
    bId = sSplit[0]
    cId = sSplit[1]

    HOST = "https://iframe.dacast.com"
    data = requests.get(f"{HOST}/b/{bId}/c/{cId}").text
    contentId = scrapers.findSingleMatch(data, r"<script\s?id=\"([^\"]+)")

    jsonUrl = f"https://playback.dacast.com/content/access?contentId={contentId}&provider=universe"
    url = requests.get(jsonUrl).json()["hls"]

    if url:
        res.Url = url
        res.ManifestType = "hls"

    return res
