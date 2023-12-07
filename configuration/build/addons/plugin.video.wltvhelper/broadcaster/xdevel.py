# -*- coding: utf-8 -*-

import requests, json
from time import time
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult

HOST = "https://play.xdevel.com"
# plugin://plugin.video.wltvhelper/play/xdevel/xxxxx
# plugin://plugin.video.wltvhelper/play/xdevel/api$aHR0cHM6Ly93d3cudGVsZXBlZ2Fzby5pdA==   # https://www.telepegaso.it


def play(search):
    res = BroadcasterResult()
    url = ""

    splitted = search.split('$')
    if len(splitted) > 1:
        return playApi(splitted[1])

    headers = utils.getBrowserHeaders()
    data = requests.get(f"{HOST}/{search}", headers=headers).text
    jsonStr = scrapers.findSingleMatch(data, r"PLAYER_CONFIG\s+=\s+(\{.+?\});\s+")
    jsonData = json.loads(jsonStr)

    station = jsonData["defaultStation"]
    channel = jsonData["stations"][station]["channel"]
    
    url = channel["sources"][0]["source"]

    # useWAS key is not always present in the "channel" dictionary
    useWas = False
    try:
        useWas = channel["useWAS"]
    except KeyError:
        pass

    if useWas:
        headers["Referer"] = f"{HOST}/{search}/{station}"
        jsonData = requests.get(f"{HOST}/was", headers=headers).json()
        was = jsonData["was"]

        headers["Origin"]  = f"{HOST}"
        headers["Referer"] = f"{HOST}/"

        url = f"{url}?wmsAuthSign={was}"
        url = f"{url}|{headers}"

    if url:
        res.Url = url
        res.Manifest = "hls"

    return res


def playApi(search):
    res = BroadcasterResult()
    url = ""

    API = "https://share.xdevel.com/api"
    search = utils.fromBase64(search)

    headers = utils.getBrowserHeaders()
    data = requests.get(f"{search}", headers=headers).text
    chKey = scrapers.findSingleMatch(data, r"xdevel.*?key=([^&]+)")
    
    #headers["Referer"] = search
    #https://share.xdevel.com/api/?platform=streamsolution&get=player&key=5d04168ba6d070135bcd35003ca848c4&ver=5
    
    dt = int(time() * 1000)

    jsonUrl = f"{API}/?platform=streamsolution&get=playersettings&key={chKey}&rdm={dt}&preview=0"
    headers["Referer"] = f"{API}/?platform=streamsolution&get=player&key={chKey}&ver=5"
    jsonData = requests.get(jsonUrl, headers=headers).json()
    key = jsonData["channels"]["0"]["key"]

    jsonUrl = f"{API}/?platform=streamsolution&get=streamingsettings&key={key}&rdm={dt}"
    headers["Referer"] = f"{API}/?platform=streamsolution&get=player&key={chKey}&ver=5"
    jsonData = requests.get(jsonUrl, headers=headers).json()
    
    urls = jsonData["params"]["playurls"]
    hlsUrl = urls["m3u8"][0]
    mpdUrl = urls["dash"][0]
    url = hlsUrl
    
    res.Url = url

    return res


#    #xdevel = chKey
#    #https://share.xdevel.com/api/?platform=streamsolution&get=player&key=5d04168ba6d070135bcd35003ca848c4&ver=5
#    #Referer: http://www.teleromauno.com/
#    #   =>
#    #       <link rel="alternate" type="application/json+oembed" href="https://share.xdevel.com/api/?platform=streamsolution&amp;get=oembed&amp;key=5d04168ba6d070135bcd35003ca848c4&amp;broadcastername=VGVsZSBSb21hIFVubw==&amp;coverurl=&amp;title=" title=""/>
#    #       <link rel="alternate" type="application/xml+oembed" href="https://share.xdevel.com/api/?platform=streamsolution&amp;get=oembed&amp;format=xml&amp;key=5d04168ba6d070135bcd35003ca848c4&amp;broadcastername=VGVsZSBSb21hIFVubw==&amp;coverurl=&amp;title=" title=""/>

#    #dt = unix milliseconds => 1679347046005
#    #https://share.xdevel.com/api/?platform=streamsolution&get=playersettings&key=5d04168ba6d070135bcd35003ca848c4&rdm=1679347046005&preview=0
#    #Referer: https://share.xdevel.com/api/?platform=streamsolution&get=player&key=5d04168ba6d070135bcd35003ca848c4&ver=5
#    #   =>
#    #       json = {"autostart":1,"muted":0,"version":"free","colorstyle":"","customcss":"","initvolume":70,"defaultsonginfo":{"artist":"","title":"","coverurl":"https://share.xdevel.com/api/player/v5/resource/logo.png"},"customstyle":{"controlsbuttonsbackground":"","metadatabackground":"","metadatatext":""},"size":{"width":640,"height":390},"channels":{"0":{"key":"57afe58c7cd8734bce9c952ad89b400f","name":"Tele Roma Uno","description":"","active":1,"parent":"","coverurl":"","filepath":"","filetype":"","overlaylogourl":"","overlaylogoposition":""}},"nobrand":0}
#    #       => key = json["channels"]["0"]["key"]
#    #       
#    #dt = unix milliseconds => 1679347046452
#    #https://share.xdevel.com/api/?platform=streamsolution&get=streamingsettings&key=57afe58c7cd8734bce9c952ad89b400f&rdm=1679347046452
#    #Referer: https://share.xdevel.com/api/?platform=streamsolution&get=player&key=5d04168ba6d070135bcd35003ca848c4&ver=5
#    #   =>
#    #       json = {"response":"ok","params":{"broadcastername":"Tele Roma Uno","broadcasterdesc":null,"primaryplayurl":"rtmp://flash2.xdevel.com:80/teleromauno/teleromauno","primaryplayurltype":"","secondaryplayurl":"https://flash2.xdevel.com/teleromauno/teleromauno/playlist.m3u8","secondaryplayurltype":"audio/mpeg","isvideo":1,"isrestreaming":0,"isondemand":0,"rtmpplayurl":"rtmp://flash2.xdevel.com:80/teleromauno","streamer":"teleromauno","alternativeplayurlmp3":"","alternativeplayurlmp3_2":"","alternativeplayurlogg":"","alternativeplayurlandroid":null,"AlternativePlayUrlProxy":null,"usepp":false,"dashplayurl":"https://flash2.xdevel.com/teleromauno/teleromauno/manifest.mpd","serviceid":"2880","playurls":{"rtmp":["rtmp://flash2.xdevel.com:80/teleromauno/teleromauno"],"m3u8":["https://flash2.xdevel.com/teleromauno/teleromauno/playlist.m3u8"],"dash":["https://flash2.xdevel.com/teleromauno/teleromauno/manifest.mpd"],"other":[]}}}
#    #       => hls = json["playurls"]["m3u8"][0]
#    #       => mpd = json["playurls"]["dash"][0]
