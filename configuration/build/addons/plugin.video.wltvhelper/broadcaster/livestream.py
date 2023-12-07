# -*- coding: utf-8 -*-

import requests
from lib.broadcaster_result import BroadcasterResult

API = "https://player-api.new.livestream.com"


def play(search):
    res = BroadcasterResult()
    url = ""

    sSplit = search.split("$")
    accountId = sSplit[0]
    eventId   = sSplit[1]

    url = requests.get(f"{API}/accounts/{accountId}/events/{eventId}/stream_info").json()["secure_m3u8_url"]

    if url:
        res.Url = url
        res.ManifestType = "hls"

    return res
