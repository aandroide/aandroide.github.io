# -*- coding: utf-8 -*-

import requests
from lib import utils, logger
from lib.broadcaster_result import BroadcasterResult

host = "https://www.dreamturk.com.tr/actions/content/media/566ab958980ea810b4658d96"


def play(search):
    res = BroadcasterResult()
    url = ""

    _json = requests.get(host).json()

    url = _json["Media"]["Link"]["ServiceUrl"] + _json["Media"]["Link"]["SecurePath"]

    if url:
        res.Url = url
        res.ManifestType = "hls"
        res.StreamHeaders = f"user-agent={utils.USER_AGENT}"

    return res
