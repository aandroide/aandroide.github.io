# -*- coding: utf-8 -*-

import requests
from lib import scrapers
from lib.broadcaster_result import BroadcasterResult


BASE_URL = "https://streamup.eu"

# https://streamup.eu/si/?can=sihd
# https://streamup.eu/si/?can=sisolocalcio
# https://streamup.eu/si/?can=silive24

STREAMUP_CHANNELS = {
    "sihd": "sihd",
    "calcio": "sisolocalcio",
    "live24": "silive24"
}


def play(search):
    res = BroadcasterResult()

    chId = STREAMUP_CHANNELS[search]

    ch_url_path = "/si/?can={}"
    response = requests.get(BASE_URL + ch_url_path.format(chId))

    # Renspose snippet
    #
    # [...]
    # jwplayer('playerGDawMEthjaAY').setup({
	# 		width: '100%',
	# 		height: "100%",
	# 		aspectratio: '16:9',
	# 		//autostart: 'true',
	# 		playlist: [{
	# 		image: "img/tappo-streaming.jpg",
	# 		sources: [
	# 			{
	# 				file: 'https://di-g7ij0rwh.vo.lswcdn.net/sportitalia/sihd/playlist.m3u8'
	# 			}
	# 			]
	# 		}],
	# 		primary: 'flash',
	# 		ga: {}
	# 	});
    # [...]
    stream_url = scrapers.findSingleMatch(response.text, r"file: '(https?:\/\/.*\.m3u8)'")
    res.Url = stream_url

    return res
