# -*- coding: utf-8 -*-

import requests, xbmcgui, urllib
from lib import config, utils, logger
from lib.broadcaster_result import BroadcasterResult
from broadcaster import rainewsrg

HOST = "https://www.raiplay.it"

def play(search):
    res = BroadcasterResult()
    res.Delay = config.getSetting("raidelay")
    url = ""

    try:
        url = play_hbbtv(search)
    except:
        url = play_raiplay(search)
    
    if url:
        result = getRealUrlAndLic(url, True)
        if result.get("drm", "") == "WIDEVINE":
            pass
        elif result.get("drm", "") == "PLAYREADY":
            result = getRealUrlAndLic(url)
        
        url = result.get("url", "")
        lic = result.get("lic", "")

        res.Url = url

        res.ManifestType = "hls"
        if ".mpd" in url:
            res.ManifestType = "mpd"

        #if lic:
            #licenseUrl = lic.get("licenceUrl", "")
            #logger.error(licenseUrl)
            #o = urllib.parse.urlparse(licenseUrl)
            #tk = o.query.split('=')[1]

            #par = '\b\u0004'
            #par = '\b\4'

            #headers=utils.getBrowserHeaders()
            #headers["Accept"] = "*/*"
            #headers["Origin"] = HOST
            #headers["Referer"] = f"{HOST}/"
            #headers["nv-authorizations"] = tk

            #licenseUrl = licenseUrl.split("?")[0]
            #license_url = "{url}/license/eme|%s|\b\x04|R{SSM}|" % urllib.urlencode(my_headers)
            #if lic:
            #    res.LicenseKey = "%s|%s|%s|R{SSM}" % (licenseUrl, headers, par)
            #    logger.error("=====>>>", res.LicenseKey)
            #    res.LicenseKey = lic + '|' + HOST + '|R{SSM}|'

    return res


def getRealUrlAndLic(url, hbbtv = False):
    lic = None
    drm = ""

    url = f"{url}&output=62"
    if hbbtv:
        url = f"{url}&forceUserAgent=raiplayappletv"

    jsonConfig = requests.get(url, headers=utils.getBrowserHeaders()).json()
    url = jsonConfig.get("video", [""])[0]
    licList = jsonConfig.get("licence_server_map", "").get("drmLicenseUrlValues", "")

    if licList:
        drm = "WIDEVINE"
        lic = next(filter(lambda l: l.get("drm", "") == drm, licList), None)
        
        if not lic:
            drm = "PLAYREADY"
            lic = next(filter(lambda l: l.get("drm", "") == drm, licList), None)

    return { "url": url, "lic": lic, "drm": drm }


def play_raiplay(search):
    url = ""
    reqUrl = "https://www.raiplay.it/dirette.json"
    jsonChannels = requests.get(reqUrl, headers=utils.getBrowserHeaders()).json()["contents"]

    for key in jsonChannels:
        channel = key["channel"]
        if search == channel:
            url = key["video"]["content_url"]
            break

    return url


def play_hbbtv(search):
    url = ""
    rai3config = config.getSetting("rai3config")
    items = getServices(search)

    service = list()
    if search == "Rai 3" and rainewsrg.isRai3NewsLive():
        service = next( iter( filter( lambda c: (c["dvbTriplet"] == rai3config), items["Service"] ) ) )
    else:
        service = items["Service"][0]
    
    if service:
        url = service.get("url", "")

    return url


def chooseRai3Region():
    rai3config = "0.0.300"
    name = ""

    try:
        items = getServices("Rai 3")
        items = items["Service"]

        suffix = "Rai 3 TGR"
        lst = list()
        li = xbmcgui.ListItem("Default HD")
        li.setProperties({"dvbTriplet": rai3config})
        lst.append(li)

        for x in items:
            if x["name"].startswith(suffix):
                title = x["name"].replace(suffix, "").strip()
                li = xbmcgui.ListItem(title)
                li.setProperties({"dvbTriplet": x["dvbTriplet"]})
                lst.append(li)

        idx = xbmcgui.Dialog().select(config.getString(30183), lst)
        if idx > 0:
            rai3config = lst[idx].getProperty("dvbTriplet")
            name = lst[idx].getLabel()
        else: return
    except:
        utils.MessageBox(30184)

    config.setSetting("rai3config", rai3config)
    config.setSetting("rai3chosen", name)


def getServices(search):
    reqUrl = "https://www.replaytvmhp.rai.it/hbbtv/launcher/RemoteControl/resources/srvConfig.json"
    items = requests.get(reqUrl).json()["Configuration"]["Editors"]["Editor"]
    items = next( iter( filter( lambda c: (c["name"].casefold() == search.casefold()), items ) ) )
    items = next( iter( filter( lambda s: (s["delivery"] == "3"), items["Services"] ) ) )
    return items