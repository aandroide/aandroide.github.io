# -*- coding: utf-8 -*-

import json, urllib, requests, html

from typing import List
from urllib.parse import urlencode

from lib.broadcaster_result import BroadcasterResult
from lib.playablemediaitem import PlayableMediaItem
from lib import utils, scrapers, logger

HOST = "https://ok.ru"

def play(search):
    res = BroadcasterResult()

    pageUrl = f"{HOST}/videoembed/{search}"
    data = requests.get(pageUrl, headers = utils.getBrowserHeaders(), verify=False).text
    jsonData = scrapers.findSingleMatch(data, r"data-options=\"([^\"]+)")
    jsonData = json.loads(jsonData.replace("&quot;", "\""))
    jsonData = json.loads(jsonData.get("flashvars", "").get("metadata", ""))

    url = jsonData.get("hlsMasterPlaylistUrl", "")
    
    if url:
        res.Url = url

    return res
