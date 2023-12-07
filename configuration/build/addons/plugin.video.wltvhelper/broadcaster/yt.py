# -*- coding: utf-8 -*-
# youtube channel & video broadcaster

#example: 
    #   #EXTINF:-1 tvg-name="VIDEO" tvg-logo="" group-title="VIDEO",Abao a Tokyo1
    #   plugin://plugin.video.wltvhelper/play/yt/c/UC84whx2xxsiA1gXHXXqKGOA/videoname

    #   plugin://plugin.video.wltvhelper/play/yt/c/@TeleuropaNetwork/Live TEN Tv

    #   #EXTINF:-1 tvg-name="VIDEO" tvg-logo="" group-title="VIDEO",VIDEO YT
    #   plugin://plugin.video.wltvhelper/play/yt/v/TbhcfUPYKEU/-

import json
import requests
from urllib.parse import unquote
from lib import scrapers, utils, logger
from lib.broadcaster_result import BroadcasterResult


HOST = "https://www.youtube.com"


def play(chtype:str,chId:str,chName:str):
    chName = unquote(chName)
    if chtype == "c":
        return playChannel(chId,chName)
    elif chtype == "v":
        return playVideo(chId)
    else:
        return playVideo(chId)


def playChannel(chId:str,chName:str):
    if chId.startswith('@'):
        videoInfoUrl = f"/{chId}"
    else:
        videoInfoUrl = f"/channel/{chId}"

    videoId = ""

    headers = utils.getBrowserHeaders();
    headers["Cookie"] ="YSC=uhMbKwwwD3g; CONSENT=YES+cb.20300101-18-p0.it+FX+133; GPS=1; VISITOR_INFO1_LIVE=NnmAzzluXtu; PREF=tz=Europe.Rome"
  
    data = requests.get(f"{HOST}{videoInfoUrl}", headers=headers).text 
    regex = r"ytInitialData\s?=\s?(.*?);<"
    jsonData = scrapers.findSingleMatch(data, regex)
    
    if not jsonData: #try with channelname
        videoInfoUrl = f"/c/{chId}"
        data = requests.get(f"{HOST}{videoInfoUrl}", headers=headers).text 
        regex = r"ytInitialData\s?=\s?(.*?);<"
        jsonData = scrapers.findSingleMatch(data, regex)

    data = None

    jsonData = json.loads(jsonData)
    tabs = jsonData["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]
    jsonData = None

    for tab in tabs:
        if tab.get("tabRenderer", {}).get("title", "") == "Home":
            homeContents = tab["tabRenderer"]["content"]["sectionListRenderer"]["contents"]
            videoId = GetLiveVideoId(chName, homeContents)
            homeContents = None
        
        if videoId: break
            
    tab = None
    tabs = None

    return playVideo(videoId)


def playVideo(videoId):
    res = BroadcasterResult()
    url = ""
    dashUrl = ""
    hlsUrl  = ""

    dashUrl, hlsUrl = GetVideoUrlDirect(videoId)

    if dashUrl:
        url = dashUrl
        res.ManifestType = "mpd"
    
    if hlsUrl:
        url = hlsUrl
        res.ManifestType = "hls"
        #res.Delay = 20

    if not url:
        logger.info("Direct url NOT found, use plugin...")
        url = GetVideoUrl(videoId)
    else:
        #res.StreamHeaders = f"user-agent={utils.USER_AGENT}"
        #url = utils.getUserAgentForLink(url)
        pass

    if url:
        res.Url = url

    return res


def GetLiveVideoId(chName, contents):
    items = []
    chName = chName.replace(" ", "").lower()

    for content in contents:
        for subContent in content["itemSectionRenderer"]["contents"]:
            for subContentValue in subContent.values():
                try:
                    items = subContentValue.get("items", [])
                    if not items:
                        ct = subContentValue.get("content", {})
                        k = next(iter(ct))
                        if k: items = ct.get(k, {}).get("items", [])
                    
                    itemIdx = -1
                    for item in items:
                        itemIdx = itemIdx+1
                        if chName == str(itemIdx): 
                            chName = ""
                        videoRenderer = item.get("videoRenderer", {})
                        for thumb in videoRenderer.get("thumbnailOverlays", []):
                            sk = next(iter(thumb))
                            if thumb[sk].get("style", "") == "LIVE":
                                videoId = GetVideoIdFromVR(videoRenderer, chName, ["title"])
                                if videoId: 
                                    return videoId
                except :
                    pass

    return ""


def GetVideoIdFromVR(videoRenderer, chName, sections):
    videoId = ""
    for section in sections:
        dictTitle = videoRenderer.get(section, {})

        if dictTitle.get("runs", []):
            title = dictTitle.get("runs", [])[0].get("text", "")

            if not title:
                title = dictTitle.get("simpleText", "")

            if chName == "" or chName in title.replace(" ", "").lower():
                videoId = videoRenderer.get("videoId", "")
        if videoId:
            break

    return videoId


def GetVideoUrl(videoId):
    url = ""

    if videoId:
        url = f"plugin://plugin.video.youtube/play/?video_id={videoId}"

    return url


def GetVideoUrlDirect(videoId):
    dashUrl = ""
    hlsUrl  = ""

    if videoId:
        data = requests.get(f"{HOST}/watch?v={videoId}", headers=utils.getBrowserHeaders()).text
        regex = r"ytInitialPlayerResponse\s?=\s?(.*?);var"
        jsonData = scrapers.findSingleMatch(data, regex)
        data = None
        jsonData = json.loads(jsonData)
        streamingData = jsonData.get("streamingData", {})
        jsonData = None

        dashUrl = streamingData.get("dashManifestUrl", "")
        hlsUrl  = streamingData.get("hlsManifestUrl", "")

        if not dashUrl and not hlsUrl:
            logger.info("No dashUrl and no hlsUrl found, get from 'formats'")
            hlsUrl = streamingData.get("formats", [])[-1].get("url", "")

    return dashUrl, hlsUrl
