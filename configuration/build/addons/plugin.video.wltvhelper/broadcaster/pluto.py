# -*- coding: utf-8 -*-

import uuid, requests, sys
from lib import logger, utils
from lib.broadcaster_result import BroadcasterResult

from urllib.parse import unquote

HOST = "https://api.pluto.tv"
UUID = uuid.uuid1().hex


def play(search):
    res = BroadcasterResult()

    search = unquote(search)
    channelsUrl = f"{HOST}/v2/channels.json?deviceId={UUID}"

    channels = {
        ch.get("slug"): ch.get("stitched", {}).get("urls", [{}])[0].get("url", "")
        for ch in requests.get(channelsUrl).json()
    }
    url = channels.get(search)

    if not url:
        channels = {
            ch.get("hash"): ch.get("stitched", {}).get("urls", [{}])[0].get("url", "")
            for ch in requests.get(channelsUrl).json()
        }
        url = channels.get(search.replace("$", "#"))

    if url:
        url = url.replace("deviceType=&", "deviceType=web&")
        url = url.replace("deviceMake=&", "deviceMake=firefox&")
        url = url.replace("deviceModel=&", "deviceModel=firefox&")
        url = url.replace("appName=&", "appName=web&")
        url = url.replace("sid=&", f"sid={UUID}&")

        res.Url = url
        res.ManifestType = "hls"

    return res
