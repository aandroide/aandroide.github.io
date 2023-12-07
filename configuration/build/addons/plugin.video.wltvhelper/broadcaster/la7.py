# -*- coding: utf-8 -*-

import requests
from lib import scrapers, utils
from lib.broadcaster_result import BroadcasterResult
from time import time

HOST = "https://www.la7.it"
LICENSE_URL = "https://la7.prod.conax.cloud/widevine/license"

headers = {
    "user-agent": utils.USER_AGENT,
    "host_token": "pat.la7.it",
    "host_license": "la7.prod.conax.cloud",
    "accept": "*/*",
    "accept-language": "en,en-US;q=0.9,it;q=0.8",
    "dnt": "1",
    "te": "trailers",
    "origin": HOST,
    "referer": HOST + "/",
}


def play(search):
    res = BroadcasterResult()

    if search == "La7":
        siteUrl = HOST + "/dirette-tv"
    elif search == "La7d":
        siteUrl = HOST + "/live-la7d"

    data = requests.get(siteUrl).text

    preAuthTokenUrl = scrapers.findSingleMatch(data, r'preTokenUrl = "(.+?)"')
    url = scrapers.findSingleMatch(data, r"""["]?dash["]?\s*:\s*["']([^"']+)["']""")

    if url:
        tokenHeader = {
            "host": headers["host_token"],
            "user-agent": headers["user-agent"],
            "accept": headers["accept"],
            "accept-language": headers["accept-language"],
            "dnt": headers["dnt"],
            "te": headers["te"],
            "origin": headers["origin"],
            "referer": headers["referer"],
        }

        preAuthToken = requests.get(preAuthTokenUrl, headers=tokenHeader, verify=False).json()["preAuthToken"]

        licenseHeader = {
            "host": headers["host_license"],
            "user-agent": headers["user-agent"],
            "accept": headers["accept"],
            "accept-language": headers["accept-language"],
            "preAuthorization": preAuthToken,
            "origin": headers["origin"],
            "referer": headers["referer"],
        }

        preLic = "&".join(["%s=%s" % (name, value) for (name, value) in licenseHeader.items()])
        tsatmp = str(int(time()))
        licenseUrl = LICENSE_URL + "?d=%s" % tsatmp
        licenseKey = "%s|%s|R{SSM}|" % (licenseUrl, preLic)

        res.Url = url
        res.ManifestType = "mpd"
        res.LicenseKey = licenseKey
        res.ManifestUpdateParameter = "full"

    return res
