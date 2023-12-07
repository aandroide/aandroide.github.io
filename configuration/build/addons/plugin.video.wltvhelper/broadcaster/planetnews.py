# -*- coding: utf-8 -*-

import requests
from lib import scrapers
from lib.broadcaster_result import BroadcasterResult

HOST = "https://planetnews.com/"
LIVE_CHANNEL_URL = "live/{}.html"

def play(search):
    res = BroadcasterResult()
    url = ""

    page_url = f"{HOST}{LIVE_CHANNEL_URL.format(search)}"
    data = requests.get(page_url).text
    
    url = scrapers.findSingleMatch(data, r"playerInstance\.setup\({\s+?file:\s?\"([^\"]+)")

    if url:
        res.Url = url

    return res
