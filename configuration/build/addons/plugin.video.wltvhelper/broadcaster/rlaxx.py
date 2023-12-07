# -*- coding: utf-8 -*-

import requests, datetime
from lib import logger, utils
from lib.broadcaster_result import BroadcasterResult

HOST = "https://app.rlaxxtv.com"
STREAM_HOST = "https://bigscreen.rlaxxtv.com"

def play(search):
    res = BroadcasterResult()

    chId = search.split("$")[1]

    header = utils.getBrowserHeaders();
    header["Origin"] = HOST
    header["Referer"] = f"{HOST}/"
    
    startDay = (datetime.datetime.utcnow() + datetime.timedelta(minutes=-30)).strftime("%Y-%m-%dT%H:%M:%S")
    endDay   = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    
    dataUrl = f"{STREAM_HOST}/api/v2/epg/channel/{chId }?content=true&startDay={startDay}&endDay={endDay}"
    jsonData = requests.get(dataUrl, headers=header).json()
    currentlyPlayingContentId = jsonData["currentlyPlaying"]["content"]["id"]

    dataUrl = f"{STREAM_HOST}/api/v2/content/{currentlyPlayingContentId}/player-setting"
    jsonData = requests.get(dataUrl, headers=header).json()

    subs = jsonData.get("captions", {}).get("url", [])
    #logger.error(subs)

    dataUrl = jsonData["streamAccess"]
    jsonData = requests.post(dataUrl, headers=header).json()

    url = jsonData["data"]["stream"]

    if url:
        res.Url = url
        #res.ManifestType = "hls"

    return res
