# Module: UnitedMusic
# Author: CrAcK75
# Created on: 09/05/2021
#

import os
import sys
import xbmcgui
import xbmcplugin
import base64
import zlib
import requests
import routing
import json
import urllib
from lib import logger, config, utils

_name = "UnitedMusic"
fileName = "listUnitedMusic.bin"

plugin = routing.Plugin()


@plugin.route("/unitedmusic")
def Start():
    ShowGenresList()


def ShowGenresList():
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, _name)

    lstItem = GetLists()
    if not lstItem:
        return

    for item in lstItem.get("worlditems", {}):
        name = item["name"]
        code = item["code"]

        li = xbmcgui.ListItem(name)
        li.setArt(
            {
                "thumb": item["ico"],
                "poster": item["thumb"],
                "fanart": item["thumb"],
            }
        )

        url = plugin.url_for(ShowStations, name, code)
        xbmcplugin.addDirectoryItem(handle, url, li, True)

    xbmcplugin.endOfDirectory(handle)


@plugin.route("/unitedmusic/showstations/<genrename>/<genrecode>")
def ShowStations(genrename, genrecode):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, genrename)
    xbmcplugin.setContent(handle, "videos")

    defaultCover = "https://www.unitedmusic.com/images/placeholder.jpg"
    infoUrlBase = "https://www.unitedmusic.com/custom_widget/finelco/getStreamInfo.jsp?host={}&radio=United_music_&idWebradio={}"

    lstItem = GetLists()
    lstItem = GetItems(genrecode, lstItem)
    for item in lstItem.get("worlditems", {}):
        code = item["code"]
        name = item["name"]

        song   = ""
        cover  = ""
        artist = ""
        year   = ""
        album  = ""
        title  = ""

        try:
            url = item["url"]
            if url == "":
                logger.debug(f"url empty on item name: {name}, code:{code}")
                continue
        except:
            logger.debug(f"url not found on item name: {name}, code:{code}")
            continue

        data = {}
        try:
            _urlInfo = GetUrlInfo(infoUrlBase, url, code, True)
            data = requests.get(_urlInfo).json()
        except:
            try:
                _urlInfo = GetUrlInfo(infoUrlBase, url, code, False)
                data = requests.get(_urlInfo).json()
            except:
                pass

        song   = data["song"]   if ("song")   in data else ""
        cover  = data["cover"]  if ("cover")  in data else ""
        artist = data["artist"] if ("artist") in data else ""
        year   = data["year"]   if ("year")   in data else ""
        album  = data["album"]  if ("album")  in data else ""
        title  = data["title"]  if ("title")  in data else ""

        if cover == "":
            cover = defaultCover

        li = xbmcgui.ListItem(name)
        li.setArt(
            {
                "thumb":  cover,
                "poster": cover,
                "fanart": cover,
            }
        )
        li.setInfo(
            "music",
            {
                "year":   year,
                "album":  album,
                "artist": artist,
                "title":  f"{name} - {artist} [{title}]",
                "mediatype": "song",
            },
        )

        li.setProperty("IsPlayable", "true")
        xbmcplugin.addDirectoryItem(handle, url, li, False)

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle)


def GetItems(code, lstItem):
    lstItem = [x for x in lstItem.get("worlditems", {}) if x["code"] == code][0]
    return lstItem


def GetLists():
    strJson = ""

    try:
        strJson = utils.decompressFile(fileName)
        strJson = json.loads(strJson)
    except Exception as e:
        strJson = ""
        logger.error("GetLists error:", e)

    if strJson == "":
        utils.MessageNotification(config.getString(30148))

    return strJson


def GetUrlInfo(infoUrlBase, url, code, replaceHttps):
    if replaceHttps:
        _urlInfo = infoUrlBase.format(urllib.parse.quote_plus(url.replace("https", "http")), code)
    else:
        _urlInfo = infoUrlBase.format(urllib.parse.quote_plus(url), code)

    return _urlInfo


plugin.run()
