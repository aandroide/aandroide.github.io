# -*- coding: utf-8 -*-

import uuid, requests

from lib import logger, utils
from lib.broadcaster_result import BroadcasterResult

HOST = "https://rakuten.tv"
API = "https://gizmo.rakuten.tv"
#UUID = uuid.uuid1().hex

headers = {
    "User-Agent": utils.USER_AGENT,
    "Content-Type": "application/json",
    "Referer": f"{HOST}/",
    "Origin": HOST
}


def play(search):
    res = BroadcasterResult()

    sSplit = search.split("$")
    cId  = sSplit[0]
    cLan = sSplit[1]
    if not cLan:
        cLan = "ITA"

    dataUrl = f"{API}/v3/avod/streamings"

    query = {
        "classification_id": 36,
        "device_identifier": "web",
        "device_stream_audio_quality": "2.0",
        "device_stream_hdr_type": "NONE",
        "device_stream_video_quality": "FHD",
        "disable_dash_legacy_packages": False,
        "locale": "it",
        "market_code": "it"
    }

    jsonPostdata = {
        "audio_language": cLan,
        "audio_quality": "2.0",
        "classification_id": "36",
        "content_id": cId,
        "content_type": "live_channels",
        "device_serial": "not implemented",
        "player": "web:HLS-NONE:NONE",
        "strict_video_quality": False,
        "subtitle_language": "MIS",
        "video_type": "stream"
    }

    json = requests.post(url=dataUrl, headers=headers, params=query, json=jsonPostdata).json()

    url = json.get("data", {}).get("stream_infos", [None])[0].get("url", "")

    if url:
        res.Url = url
        res.ManifestType = "hls"

    return res
