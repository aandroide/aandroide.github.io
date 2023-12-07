# -*- coding: utf-8 -*-

import requests

from lib import utils
from lib.broadcaster_result import BroadcasterResult
from datetime import datetime, timezone

HOST = "https://olympics.com"

headers = {"User-Agent": utils.USER_AGENT, "Referer": HOST}


def play(search):
    res = BroadcasterResult()

    ts = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

    urlBase = ""
    url = ""
    jsonChannels = requests.get(HOST + "/it/api/v1/d3vp/epgchannels/linear/live-channels").json()

    for ch in jsonChannels:
        if ch["slug"] == search:
            urlBase = ch["src"]

    if urlBase:
        tokenUrl = f"{HOST}/tokenGenerator?url={urlBase}&domain=https://ott-dai-oc.akamaized.net&_ts={ts}"
        url = requests.get(tokenUrl).json()

    if url:
        res.Url = f"{url}|user-agent={utils.USER_AGENT}"

    return res
