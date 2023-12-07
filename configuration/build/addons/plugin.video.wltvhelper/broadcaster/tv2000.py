# -*- coding: utf-8 -*-

import requests
from lib import scrapers, xmltodict
from lib.broadcaster_result import BroadcasterResult


HOST = "https://diretta.tv2000.it/"
DRM_API_URL = "api/drm/status"
LIVE_CHANNEL_URL = "?channel=tv2000_live"
M3U8_XML_URL = "https://mediatv2000-meride-tv.akamaized.net/proxy/bulkproxynew/embedproxy_bulk.php/{}/tv2000/desktop/NO_LABEL/f4m/default/aHR0cHM6Ly9kaXJldHRhLnR2MjAwMC5pdC8q"


def play(search):
    res = BroadcasterResult()

    url = ""
    idChannel = ""
    var2Find = ""
    widevineLicenseUrl = "https://widevine-dash.ezdrm.com/proxy?pX=A90BE1"

    isDrmJson = requests.get("{}{}".format(HOST, DRM_API_URL)).json()
    isDrm = isDrmJson["active"] == "true"
    strXml = ""

    data = requests.get("{}{}".format(HOST, LIVE_CHANNEL_URL)).text

    if isDrm:
        res.ManifestType = "mpd"
        var2Find = "playreadyEmbedID"
    else:
        var2Find = "nonRestrictedEmbedID"

    idChannel = scrapers.findSingleMatch(data, r'var\s{}\s=\s"(.*?)"'.format(var2Find))

    strXml = requests.get(M3U8_XML_URL.format(idChannel)).text
    xml = xmltodict.parse(strXml)
    url = xml["embed"]["video"]["default"]

    if url:
        res.Url = url

    return res
