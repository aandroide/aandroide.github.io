# -*- coding: utf-8 -*-

import requests, uuid
from lib import config, utils, logger
from lib.broadcaster_result import BroadcasterResult

mpd = config.getSetting("mpd")

HOST = "https://www.discoveryplus.com"

def play(search):
    res = BroadcasterResult()
    chId = ""
    
    deviceId = uuid.uuid4().hex
    
    headers = utils.getBrowserHeaders()

    headers.pop("Upgrade-Insecure-Requests")
    headers["Accept"] = "*/*"
    headers["Origin"] = HOST
    headers["Referer"] = f"{HOST}/"
    headers["Access-Control-Request-Method"] = "GET"
    headers["Access-Control-Request-Headers"] = "x-disco-client,x-disco-params"

    infoUrl = "https://global-prod.disco-api.com/bootstrapInfo"
    requests.options(infoUrl, headers=headers)

    headers.pop("Access-Control-Request-Method")
    headers.pop("Access-Control-Request-Headers")

    headers["x-disco-client"] = "WEB:UNKNOWN:dplus_us:2.21.0"
    headers["x-disco-params"] = "bid=dplus,hn=www.discoveryplus.com,hth=it"
   
    jsonData = requests.get(infoUrl, headers=headers).json()
    baseApiUrl = jsonData.get("data", {}).get("attributes", {}).get("baseApiUrl", "")

    #get token
    headers.pop("x-disco-params")
    headers["x-disco-params"] = "realm=dplay,bid=dplus,hn=www.discoveryplus.com,hth=,features=ar"
    headers["x-device-info"]  = f"dplus_us/2.21.0 (desktop/desktop; Windows/NT 10.0; {deviceId})"
    
    token = requests.get(f"{baseApiUrl}/token?deviceId={deviceId}&realm=dplay&shortlived=true", headers=headers).json()["data"]["attributes"]["token"]
    cookies = { "st": token }
    #headers["If-None-Match"] = 'W/"926244521"'

    chs = requests.get(f"{baseApiUrl}/cms/routes/home?include=default&decorators=playbackAllowed", headers=headers, cookies=cookies).json()["included"]
    chs = list(filter(lambda x: x.get("type", "") == "channel", chs))
    
    for key in chs:
        if (key.get("attributes", {}).get("hasLiveStream", "") == True
            and "Free" in key.get("attributes", {}).get("packages", [])
            and search == key["attributes"]["channelCode"]):
            chId = key["id"]
            break
    chs = None

    if chId:
        postJsonData = f'{{ "channelId": "{chId}", "deviceInfo": {{ "adBlocker": false, "drmSupported": true }}, "wisteriaProperties": {{ "siteId": "dplus_it", "platform": "mobile" }} }}'

        headers.pop("x-device-info")
        headers["x-disco-client"] = "WEB:UNKNOWN:dplus_us:27.38.0"
        headers["x-disco-params"] = "realm=dplay,siteLookupKey=dplus_it,bid=dplus,hn=www.discoveryplus.com,hth=it"
        headers["content-type"] = "application/json"
        
        jsonData = requests.post(f"{baseApiUrl}/playback/v3/channelPlaybackInfo", headers=headers, cookies=cookies, data=postJsonData).json()
        data = jsonData.get("data", {}).get("attributes", {}).get("streaming", {})[0]
        jsonData = None

        if data["protection"]["drmEnabled"] == True and mpd:
            res.ManifestType = "mpd"
            res.LicenseKey = (
                data["protection"]["schemes"]["widevine"]["licenseUrl"]
                + "|preauthorization="
                + data["protection"]["drmToken"]
                + "|R{SSM}|"
            )
            #res.LicenseType = "com.widevine.alpha"
        else:
            res.ManifestType = "hls"
            
        #res.PlayerMode = 1

        res.Url = data["url"]
        
    return res
