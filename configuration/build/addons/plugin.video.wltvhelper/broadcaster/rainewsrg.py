# -*- coding: utf-8 -*-

import requests, json, xbmcgui
from datetime import datetime
from lib import scrapers, config, utils, logger
from lib.broadcaster_result import BroadcasterResult

HOST = "https://www.rainews.it"

mpd = config.getSetting("mpd")


def play(search):
    res = BroadcasterResult()

    url = ""
    isLive = False
    sSplit = search.split("$")

    data = requests.get(f"{HOST}/tgr/{sSplit[0]}/notiziari").text

    strWashiContext = scrapers.findSingleMatch(data, r'WashiContext.*parse\(\"(.*?)\"\);\s+</script')
    isWashi = strWashiContext != ""
    
    if isWashi:
        strWashiContext = strWashiContext.replace('\\"', '"')
        strJson = json.loads(strWashiContext)
        strWashiContext = None

        isLive = strJson["itemToPlay"]["data_type"] == "diretta"
        matchedUrl = strJson["itemToPlay"]["content_url"]
        
        if isLive:
            url = matchedUrl
        else:
            url = getItemToView(strJson["fasce"])
    else:
        url = scrapers.findSingleMatch(data, r'data-mediaurl="([^"]+)')
        
    if url and url != "x":
        url = requests.get(f"{url}&output=47", headers=utils.getBrowserHeaders()).json().get("video", [""])[0]

        if "mpd" in url:
            res.ManifestType = "mpd"

    res.Url = url

    return res


def getItemToView(jsonFasce):
    lstItem = list()

    jsonArchive = next(x for x in jsonFasce if x["title"] == "Archivio")["contents"]
    
    lst=list()
    for x in jsonArchive:
        lst.append(x["title"])
    idx = xbmcgui.Dialog().select(config.getString(30185), lst)

    if idx < 0: return "x"
    winTitle = lst[idx]

    jsonSearch  = next(x for x in jsonArchive if x["title"] == lst[idx])

    for card in jsonSearch["cards"]:
        date  = card["broadcast"]["edition"]["date"] 
        title = card["broadcast"]["edition"]["title"]
        title = f"{date} {title}"
        url   = card["content_url"]
        img   = card["image"]["media_url"]
        img   = f"{HOST}{img}"

        lstItem.append(utils.getListItem(title, url, mediatype="video", isFolder=False))
    
    idx = xbmcgui.Dialog().select(f"{config.getString(30185)} {winTitle}", lstItem)
    if idx < 0: return "x"

    url = lstItem[idx].getPath()

    return url


def isRai3NewsLive():
    isLive = False
    schedule = requests.get( HOST + "/dl/rai24/assets/json/palinsesto-tgr.json" ).json()
    weekday = [1, 2, 3, 4, 5, 6, 0]
    today = datetime.now()
    date = today.date()
    dayNumber = weekday[today.weekday()]
    hour = today.hour * 60 + today.minute

    for key, value in schedule.items():
        if (key == "TGR"):
            for v in value:
                start = int(v["from"].split(":")[0]) * 60 + int(v["from"].split(":")[1])
                end = int(v["to"].split(":")[0]) * 60 + int(v["to"].split(":")[1])
                if start <= hour < end and ( "days" in v and dayNumber in v["days"] or "day" in v and v["day"] == date ):
                    isLive = True
                    break

    return isLive