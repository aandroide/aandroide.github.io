# -*- coding: utf-8 -*-

import requests
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult

# plugin://plugin.video.wltvhelper/play/telelombardia/topcalcio24

HOST = "https://telelombardia.video"


def play(search):
    res = BroadcasterResult()
    url = ""

    headers = utils.getBrowserHeaders()
    req = requests.Session()
    req.get(HOST, headers=headers)

    tmpUrl = f"{HOST}/video/index"
    data = req.get(tmpUrl, headers=headers).text
    token = scrapers.findSingleMatch(data, r"name=\"csrf-token\"\scontent=\"([^\"]+)\"")
    data = None

    req.get(f"{HOST}/site/setdeviceidintosession", headers=headers)

    formData = {"rel": 0, "_csrf": token}
    jsonData = req.post(f"{HOST}/video/getfoldervideolist", headers=headers, data=formData).json()

    channels = jsonData.get("channelList", [])
    jsonData = None
    channel = next( iter( filter( lambda c: (c.get("channel_name", "").replace(" ", "").lower() == search.lower()), channels ) ) )
    chId = channel.get("id", 0);

    referer = f"{HOST}/video/viewlivestreaming?rel={chId}&cntr=0"

    headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
    headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
    headers["X-Requested-With"] = "XMLHttpRequest"
    headers["Origin"] = HOST
    headers["Referer"] = referer
    
    formData.pop("rel")
    formData["channel"] = chId

    tmpUrl = f"{HOST}/video/getlivestreaminginevidence"
    jsonData = req.post(tmpUrl, headers=headers, data=formData).json()

    url = jsonData .get("urlVideo", [])[0].get("url", "")

    if url:
        res.Url = url
        #res.ManifestType = "mpd" if mpd else "hls"

    return res
