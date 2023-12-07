# -*- coding: utf-8 -*-

import requests
from lib import utils
from lib.broadcaster_result import BroadcasterResult

HOST = "https://www.redbull.com"

headers = {
    "user-agent": utils.USER_AGENT,
    "accept": "*/*",
    "accept-language": "en,en-US;q=0.9,it;q=0.8",
    "origin": HOST,
    "referer": HOST+"/",
}


def play(search):
    res = BroadcasterResult()

    url = ""
    tokenurl = "https://api.redbull.tv/v3/session?os_family=http"
    strtoken = requests.get(tokenurl, headers=headers, verify=False).json()["token"]
    url = "https://dms.redbull.tv/v3/linear-borb/%s/playlist.m3u8" % strtoken

    if(url):
        res.Url = url

    return res
