# -*- coding: utf-8 -*-

import requests
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult

HOST = "https://it-it.wedotv.com/"

#use: plugin://plugin.video.wltvhelper/play/wedotv/wedobigdocs

def play(search):
    res = BroadcasterResult()
    url = ""

    url = GetUrl(HOST, search)

    if url:
        res.Url = url
        res.ManifestType = "hls"

    return res

def GetUrl(host, search):
    pageUrl = f"{host}channels?program={search}"
    data = requests.get(pageUrl, headers = utils.getBrowserHeaders()).text
    url = scrapers.findSingleMatch(data, r'<source\r*?\s*src="([^"]+)') 

    return url
