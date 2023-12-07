# -*- coding: utf-8 -*-

import requests
from lib import logger
from lib.broadcaster_result import BroadcasterResult


def play(search):
    res = BroadcasterResult()

    url = ""
    reqUrl = "https://www.raiplaysound.it/dirette.json"
    json = requests.get(reqUrl).json()["contents"]

    for key in json:
        channel = key["channel"]["category_path"]
        if search == channel:
            url = key["audio"]["url"]
            break

    if url:
        res.Url = requests.get(url).url if "relinkerServlet" in url else url

    return res
