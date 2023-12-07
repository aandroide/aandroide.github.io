# -*- coding: utf-8 -*-

import requests, json, uuid
from urllib.parse import urlencode
from lib import scrapers, utils, config, logger
from lib.broadcaster_result import BroadcasterResult

HOST = "https://www.mtv.it"


def play(search):
    res = BroadcasterResult()
    url = ""

    deviceId = uuid.uuid4()
    #deviceId = str(uuid.uuid1())

    urlChannel = HOST + "/diretta-tv/1iwm9n"
    data = requests.get(urlChannel, headers=utils.getBrowserHeaders()).text
    jsonData = scrapers.findSingleMatch(data, r"window\.__DATA__\s=\s([^\n]+);")
    jsonData = json.loads(jsonData)

    mgid = ""
    urlJsonChannel = ""
    for child1 in jsonData["children"]:
        if(child1["type"] == "MainContainer"):
            for child2 in child1["children"]:
                if(child2["type"] == "FlexWrapper"):
                    for child3 in child2["children"]:
                        if(child3["type"] == "Player"):
                            mgid = child3["props"]["videoDetail"]["mgid"]
                            urlJsonChannel = child3["props"]["videoDetail"]["videoServiceUrl"]
                            break

    parameters = {
        "clientPlatform":"desktop",
        "ssus": deviceId,
        "tveprovider":"",
        "browser" : "Chrome",
        "device": "Desktop",
        "os":"Windows+10"
    }

    if mgid:
        urlChannel = f"{urlJsonChannel.split('?')[0]}?{urlencode(parameters)}"
        jsonData = requests.get(urlChannel, headers=utils.getBrowserHeaders()).json()
        url = jsonData.get("stitchedstream", "").get("source", "")

    if url:
        res.Url = url
        # res.ManifestType = "hls"

    return res
