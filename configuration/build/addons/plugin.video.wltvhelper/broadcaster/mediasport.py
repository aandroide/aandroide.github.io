# -*- coding: utf-8 -*-

import requests
from lib import scrapers, logger
from lib.broadcaster_result import BroadcasterResult


def play(search):
    res = BroadcasterResult()
    url = ""

    if search == "extra":
        pageUrl = "https://mschannel.tv/extra"
    elif search == "acisport":
        pageUrl = "https://www.msmotor.tv/aci"
    else:
        pageUrl = "https://{}.tv".format(search)

    data = requests.get(pageUrl).text
    url = scrapers.findSingleMatch(data, r'<source\ssrc="([^"]+)"\stype="application/x-mpeg')

    res.Url = url

    return res
