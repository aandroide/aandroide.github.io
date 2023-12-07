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

_name = "YouTubeMusic"
fileName = "listYouTubeMusic.bin"

plugin = routing.Plugin()


@plugin.route("/youtubemusic")
def Start():
    ShowGroups()


def ShowGroups():
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, _name)

    lstItem = GetLists()
    if not lstItem:
        return

    #"Groups":["Karaoke","Music","Relax"],"Channels":
    lstGroups = lstItem.get("Groups", [])
    if not lstGroups:
        return

    for group in lstGroups:
        li = xbmcgui.ListItem(group)

        url = plugin.url_for(ShowChannels, group)
        xbmcplugin.addDirectoryItem(handle, url, li, True)

    xbmcplugin.endOfDirectory(handle)

@plugin.route("/youtubemusic/showchannels/<group>")
def ShowChannels(group):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, _name)

    lstItem = GetChannels(group, GetLists())
    if not lstItem:
        return

    for item in lstItem: 
        name = item["Name"]
        group = item["Group"]
        code  = item["ChannelId"]
        genre = item["Genre"]
        descr = item["Description"]

        itemName = f"{name} - {group}"

        li = xbmcgui.ListItem(itemName)
        li.setInfo("video", {"title": itemName, "genre": genre, "mediatype": "music", "plot": descr})
        li.setArt(
            {
                "thumb":  item["Logo"],
                "poster": item["Logo"],
                "fanart": item["Logo"],
            }
        )

        url = plugin.url_for(ShowVideos, itemName, code)
        xbmcplugin.addDirectoryItem(handle, url, li, True)

    xbmcplugin.endOfDirectory(handle)


@plugin.route("/youtubemusic/showvideos/<name>/<code>")
def ShowVideos(name, code):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, name)
    xbmcplugin.setContent(handle, "videos")

    lstItem = GetChannel(code, GetLists())

    for item in lstItem.get("Videos", []):
        title = item["Title"]
        logo  = item["Logo"]
        url   = item["KodiUrl"]
        
        song   = ""
        artist = lstItem["Name"]
        genre  = lstItem["Genre"]
        year   = ""
        album  = ""

        li = xbmcgui.ListItem(title)
        li.setArt(
            {
                "thumb":  logo,
                "poster": logo,
                "fanart": logo,
            }
        )
        li.setInfo(
            "video",
            {
                "year":   year,
                "album":  album,
                "artist": [artist],
                "title":  f"{title} - {artist}",
                "mediatype": "song",
            },
        )

        li.setProperty("IsPlayable", "true")
        xbmcplugin.addDirectoryItem(handle, url, li, False)

    xbmcplugin.endOfDirectory(handle)


def GetChannels(group, lstItem):
    return list(filter(lambda item: item["Group"] == group, lstItem.get("Channels", [])))


def GetChannel(code, lstItem):
    return [x for x in lstItem.get("Channels", []) if x["ChannelId"] == code][0]


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


plugin.run()
