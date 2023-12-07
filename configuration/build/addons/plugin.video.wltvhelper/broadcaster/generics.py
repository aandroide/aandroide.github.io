# -*- coding: utf-8 -*-

import requests, uuid, html, json
from lib import scrapers, config, utils, logger
from lib.broadcaster_result import BroadcasterResult
from time import time

# plugin://plugin.video.wltvhelper/play/generics/search

mpd = config.getSetting("mpd")
res = BroadcasterResult()


def play(search):
    search = search.lower()
    #parameter = search.split('$')

    options = {
        "acisport": GetACI,
        "cilentano": GetCilentano,
        "cilentanouno": GetCilentano1,
        "cilentanodue": GetCilentano2,
        "cilentanotre": GetCilentano3,
        "koper": GetKoper,
        "bandwtv": GetBandw,
        "laq": GetLaqTV,
        "canale88": GetCanale88,
        "canale58": GetCanale58,
        "telesardegna": GetTelesardegna,
        "nolink": GetNoLink,
    }

    if search not in options.keys():
        search = "nolink"

    return options[search]()


def GetNoLink():
    return res


def GetACI():
    url = ""
    HOST = "https://www.acisport.it/aci-sport-tv.asp"
    data = requests.get(HOST).text
    pageUrl = scrapers.findSingleMatch(data, r"iframe\ssrc=\"([^\"]+)")
    data = requests.get(pageUrl).text
    pageUrl = scrapers.findSingleMatch(data, r"\)\.src=\"([^\"]+)")
    dataJson = requests.get(f"{pageUrl}/json").json()
    url = dataJson.get("n3CDNPlaylist", "")

    if url:
        res.Url = url

    return res


def GetCilentano(ch):
    url = ""
    
    HOST = "https://cilentano.tv"

    if not ch:
        API = "https://player-backend.restream.io/public/videos/"
        data = requests.get(f"{HOST}").text
        token = scrapers.findSingleMatch(data, r'token=([^"]+)')
        #_url  = scrapers.findSingleMatch(data, r'iframe\sid=\"r-embed-player-iframe\"\ssrc=\"([^"]+)')
        jsonData = requests.get(f"{API}{token}").json()
        url = jsonData["videoUrlHls"]

        if mpd:
            url = jsonData["videoUrlDash"]
            res.ManifestType = "mpd"
    else:
        page = ""
        if ch == 1:
            page = "/canaleuno/"
        elif ch == 2:
            page = "/canaledue/"
        elif ch == 2:
            page = "/canaletre/"

        if page:
            data = requests.get(f"{HOST}{page}").text
            jsonData = scrapers.findSingleMatch(data, r'data-options="([^"]+)')
            jsonData = html.unescape(jsonData)
            jsonData = json.loads(jsonData)
            
            url = jsonData.get("videos", [])[0].get("mp4HD", "")
            if not url:
                url = jsonData.get("videos", [])[0].get("mp4SD", "")

    if url:
        res.Url = url

    return res


def GetCilentano1():
    return GetCilentano(1)
def GetCilentano2():
    return GetCilentano(2)
def GetCilentano3():
    return GetCilentano(3)


def GetKoper():
    # Testing after some weeks it did not change
    CLIENT_ID = "82013fb3a531d5414f478747c1aca622"
    API = "https://api.rtvslo.si"

    jsonUrl = f"{API}/ava/getLiveStream/tv.kp1?client_id={CLIENT_ID}"
    jsonData = requests.get(jsonUrl).json()

    urlHost = jsonData.get("response", {}).get("mediaFiles", [])[0].get("streamer", "")
    urlPath = jsonData.get("response", {}).get("mediaFiles", [])[0].get("file", "")

    if urlHost and urlPath:
        res.Url = urlHost + urlPath

    return res


def GetBandw():
    HOST = "https://www.bandw.tv/"
    url = ""

    pageUrl = ""
    data = requests.get(HOST).text
    if data:
        pageUrl = scrapers.findSingleMatch(data, r'<iframe src="([^"]+)"')
    
    if pageUrl:
        data = requests.get(pageUrl).text
        if data:
            url = scrapers.findSingleMatch(data, r"src: '([^']+)'")

    if url:
        res.Url = url 

    return res


def GetLaqTV():
    url = ""
    HOST = "https://www.aqbox.tv/streaming.php"
    data = requests.get(f"{HOST}").text
    alias = scrapers.findSingleMatch(data, r"mtm_webcam',\s'([^']+)")
    now = str(int(time()))

    jsonUrl = f"https://player.ipcamlive.com/player/getcamerastreamstate.php?_={now}&token=&alias={alias}&targetdomain=www.aqbox.tv&getstreaminfo=1"
    jsonData = requests.get(jsonUrl).json()

    url0 = jsonData["details"]["address"]
    url1 = jsonData["details"]["streamid"]
    url2 = jsonData["streaminfo"]["live"]["levels"][0]["url"]

    url = f"{url0}streams/{url1}/{url2}".replace("http", "https")

    if url:
        res.Url = url

    return res


def GetCanale88():
    url = ""
    REFERER = "https://ott.streann.com"
    HOST = "https://ott3.streann.com"
    
    source = utils.toBase64("www.nslradiotv.it")
    webPlayerId = "aa85f95b-1551-4851-bc3a-691063421b0b"
    resellerId = "5cb6a1682cdc8fec6b9ae8fd"
    channelId = "5d6001f02cdca9c62bcbf9f6"

    headers = utils.getBrowserHeaders()
    headers["Origin"] = REFERER
    headers["Referer"] = f"{REFERER}/"

    serverTimeUrl = f"{HOST}/web/services/public/get-server-time"
    serverTime = requests.get(serverTimeUrl, headers=headers).json()["serverTime"]
    serverTime = str(serverTime)

    deviceId = f"{str(uuid.uuid4())}{str(uuid.uuid4())}"
    deviceId = deviceId.replace("-", "")[:50]
    jsonUrl = f"{HOST}/loadbalancer/services/web-players/{webPlayerId}/token/channel/{channelId}/{deviceId}"

    argsData = { "arg1": source, "arg2": utils.toBase64(serverTime) }
    jsonData = requests.post(jsonUrl, headers=headers, data=argsData).json()
    token = jsonData["token"]
    lcltime = int(time() * 1000)

    jsonUrl = f"https://ott3.streann.com/loadbalancer/services/web-players/channels-reseller-secure/{channelId}/{webPlayerId}/{token}/{resellerId}/playlist.m3u8?date={lcltime}&arg1={source}&device-type=web&device-name=web&device-os=web&device-id={deviceId}&doNotUseRedirect=true"
    url = requests.get(jsonUrl, headers=headers).json()["url"]

    if url:
        res.Url = url

    return res


def GetCanale58():
    from .helper import wimtv
    HOST = "https://www.canale58.com/"
    return wimtv.GetWimUrl(HOST)


def GetTelesardegna():
    from .helper import wimtv
    HOST = "https://telesardegna.net/"
    return wimtv.GetWimUrl(HOST)

