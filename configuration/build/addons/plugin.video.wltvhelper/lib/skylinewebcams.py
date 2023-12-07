# -*- coding: utf-8 -*-
# Module: SkyLineWebCams
# Author: CrAcK75
# Created on: 09/05/2021
#
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
from lib import logger, config, utils

_name = "SkyLineWebCams"
fileName = f"list{_name}.bin"
plugin = routing.Plugin()


@plugin.route("/skylinewebcams")
def Start():
    ShowContinentsList()


def ShowContinentsList():
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, _name)

    imagedir = "world"
    lstItem = GetLists()
    if (not lstItem): return

    for item in lstItem["worlditems"]:
        name = item["name"]
        code = item["code"]
        png = "{}.png".format(code)

        li = xbmcgui.ListItem(name)
        li.setArt(GetArt(png))
        #li.setArt({
        #    "thumb": os.path.join(config.ADDONPATH, "resources", imagedir, png),
        #    "poster": os.path.join(config.ADDONPATH, "resources", imagedir, png),
        #    "fanart": os.path.join(config.ADDONPATH, "resources", imagedir, png),
        #    })

        url = plugin.url_for(ShowCountries, code)
        xbmcplugin.addDirectoryItem(handle, url, li, True)

    xbmcplugin.endOfDirectory(handle)


@plugin.route("/skylinewebcams/showcountries/<continentcode>")
def ShowCountries(continentcode):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, continentcode)

    lstItem = GetLists()
    lstItem = GetItems(continentcode, lstItem)
    for item in lstItem.get("worlditems", {}):
        code = item["code"]
        name = item["name"]
        png = "{}.png".format(code)

        li = xbmcgui.ListItem(name)
        li.setArt(GetArt(png))

        url = plugin.url_for(ShowRegions, continentcode, code)
        xbmcplugin.addDirectoryItem(handle, url, li, True)

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle, True)


@plugin.route("/skylinewebcams/showregion/<continentcode>/<countrycode>")
def ShowRegions(continentcode, countrycode):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, countrycode)

    lstItem = GetLists()
    lstItem = GetItems(continentcode, lstItem)
    lstItem = GetItems(countrycode, lstItem)

    for item in lstItem.get("worlditems", {}):
        code = item["code"]
        name = item["name"]
        png = "{}.png".format(code)

        li = xbmcgui.ListItem(name)
        li.setArt(GetArt(png))

        url = plugin.url_for(ShowCities, continentcode, countrycode, code)
        xbmcplugin.addDirectoryItem(handle, url, li, True)

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle, True)


@plugin.route("/skylinewebcams/showcities/<continentcode>/<countrycode>/<regioncode>")
def ShowCities(continentcode, countrycode, regioncode):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, regioncode)

    lstItem = GetLists()
    lstItem = GetItems(continentcode, lstItem)
    lstItem = GetItems(countrycode, lstItem)
    lstItem = GetItems(regioncode, lstItem)
    for item in lstItem.get("worlditems", {}):
        code = item["code"]
        name = item["name"]
        png = "{}.png".format(code)

        li = xbmcgui.ListItem(name)
        li.setArt(GetArt(png))

        url = plugin.url_for(ShowWebCams, continentcode, countrycode, regioncode, code)
        xbmcplugin.addDirectoryItem(handle, url, li, True)

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle, True)


@plugin.route("/skylinewebcams/showwebcams/<continentcode>/<countrycode>/<regioncode>/<citycode>")
def ShowWebCams(continentcode, countrycode, regioncode, citycode):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, citycode)
    xbmcplugin.setContent(handle, "videos")

    imagedir = ""
    lstItem = GetLists()
    lstItem = GetItems(continentcode, lstItem)
    lstItem = GetItems(countrycode, lstItem)
    lstItem = GetItems(regioncode, lstItem)
    lstItem = GetItems(citycode, lstItem)
    for item in lstItem.get("worlditems", {}):
        code = item["code"]
        name = item["name"]
        descr = item["description"]
        thumb = item["thumb"]
        url = item["url"]
        png = "webcam.png"

        li = xbmcgui.ListItem(name)
        li.setInfo("video", {"title": name, "genre": _name, "mediatype": "video", "plot": descr})
        li.setArt({
            #"icon": os.path.join(config.ADDONPATH, "resources", icon),
            "thumb": thumb,
            "poster": thumb,
            "fanart": thumb,
            })
        li.setProperty("IsPlayable", "true")
        xbmcplugin.addDirectoryItem(handle, url, li, False)

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle)


def GetItems(code, lstItem):
    lstItem = [x for x in lstItem["worlditems"] if x["code"] == code][0]
    return lstItem


def GetArt(icon):
    return {
            #"icon": os.path.join(config.ADDONPATH, "resources", icon),
            #"thumb": os.path.join(config.ADDONPATH, "resources", icon),
            "poster": GetPoster(),
            "fanart": GetFanArt(),
            }


def GetPoster():
    return os.path.join(config.ADDON_PATH, "resources", "bg", _name + ".png")


def GetFanArt():
    return os.path.join(config.ADDON_PATH, "resources", "bg", _name + ".png")


def GetLists():
    strJson = ""

    try :
        strJson = utils.decompressFile(fileName)
        strJson = json.loads(strJson)
    except Exception as e:
        strJson = ""
        logger.error("GetLists error:", e)

    if strJson == "":
        utils.MessageNotification(config.getString(30148))

    return strJson

plugin.run()
