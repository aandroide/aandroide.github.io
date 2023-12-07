# -*- coding: utf-8 -*-

import requests
from lib import config, logger
from lib.broadcaster_result import BroadcasterResult

BASEURL = "https://il.srgssr.ch/integrationlayer/2.0/mediaComposition/byUrn/%s.json?onlyChapters=false&vector=portalplay"

mpd = config.getSetting("mpd")

headers = {
    "Host": "srg.live.ott.irdeto.com",
    "Content-Type": "",
}


def play(search):
    res = BroadcasterResult()

    url = ""
    protocol = "DASH" if mpd else "HLS"
    drmType = "WIDEVINE" if mpd else "FAIRPLAY"
    licenseUrl = ""

    jsonData = requests.get("https://www.rsi.ch/play/v3/api/rsi/production/tv-livestreams").json()["data"]

    for item in jsonData:
        if search == item["title"]:
            livestreamUrn = item["livestreamUrn"]
            urlStreams = BASEURL % livestreamUrn
            chapterList = requests.get(urlStreams).json()["chapterList"]

            for resourceList in chapterList[0]["resourceList"]:
                if resourceList["protocol"] == protocol:
                    _found = resourceList
                    break

            if _found:
                url = _found["url"]

                for drm in _found["drmList"]:
                    if drm["type"] == drmType:
                        licenseUrl = drm["licenseUrl"]
                        break

    if url:
        res.ManifestType = "mpd" if mpd else "hls"
        licenseHeader = "&".join(["%s=%s" % (name, value) for (name, value) in headers.items()])
        licenseKey = "%s|%s|R{SSM}|" % (licenseUrl, licenseHeader)

        res.Url = url
        res.LicenseKey = licenseKey
        res.ManifestUpdateParameter = "full"

    return res
