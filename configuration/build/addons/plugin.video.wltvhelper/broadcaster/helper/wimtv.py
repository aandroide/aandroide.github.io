# -*- coding: utf-8 -*-

import requests
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult


def GetWimUrl(HOST):
    res = BroadcasterResult()
    url = ""

    TOKENHOST = "https://platform.wim.tv"
    tokenUrl = f"{TOKENHOST}/wimtv-server/oauth/token"

    headers = utils.getBrowserHeaders()

    data = requests.get(HOST, headers=headers).text
    #data = scrapers.findSingleMatch(data, r'<iframe.*\.wim\.tv.*</iframe>')
    pageUrl = scrapers.findSingleMatch(data, r'<iframe.*?src="([^"]+)"')

    headers["Referer"] = pageUrl
    headers["Authorization"] = "Basic d3d3Og=="
    
    argsData = { "grant_type": "client_credentials" }
    jsonData = requests.post(tokenUrl , headers=headers, data=argsData).json()
    token = jsonData["access_token"]

    chId = pageUrl.split('=')[-1]
    jsonUrl = f"{TOKENHOST}/wimtv-server/api/public/live/channel/{chId}/play"

    headers["Accept-Language"] = "it"
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"
    headers["X-Wimtv-timezone"] = "3600000"
    headers["Origin"] = TOKENHOST
    headers["Accept"] = "application/json"
    headers["X-Requested-With"] = "XMLHttpRequest"

    jsonData = requests.post(jsonUrl, headers=headers, json={}).json()

    url = jsonData["srcs"][0]["uniqueStreamer"]

    if url:
        res.Url = url

    return res