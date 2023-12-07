# Module: WorldRadio
# Author: CrAcK75
# Created on: 06/05/2021
#

import os
import sys
import xbmcgui, xbmcplugin, json
import requests
import routing

from typing import List
from lib import logger, config, utils
from lib.m3u.m3uitem import M3UItem
from lib.m3u.m3uparser import M3UParser, M3UStreamType

_name = "WorldRadio"
fileName = f"list{_name}Idx.bin"
plugin = routing.Plugin()


@plugin.route("/worldradio")
def Start():
    ShowCuntriesList()


def ShowCuntriesList():
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, "International Radios")

    lstItem = GetLists()
    if not lstItem:
        return

    for item in lstItem:
        name = item["name"]
        code = item["code"]

        utils.addMenuItem(handle, name, plugin.url_for(ShowCities, code), "world", code)

    xbmcplugin.endOfDirectory(handle)


#@plugin.route("/worldradio/showcountries/<code>")
#def ShowCountries(countrycode):
#    handle = plugin.handle
#    xbmcplugin.setPluginCategory(handle, continentcode)

#    lstItem = GetLists()
#    lstItem = GetItems(continentcode, lstItem)
#    for item in lstItem.get("worlditems", {}):
#        code = item["code"]
#        name = item["name"]
#        url = item["url"]

#        if code == "it":
#            continue

#        utils.addMenuItem(handle, name, plugin.url_for(SwitchList, name, url), "flags", code, fanart="background.png")

#    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
#    xbmcplugin.endOfDirectory(handle, True)

@plugin.route("/worldradio/showcities/<countrycode>")
def ShowCities(countrycode):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, "radios")

    lstItem = GetCountryCities(countrycode)
    countries = lstItem.get("countries", [])
    
    if countries:
        cities = countries[0].get("places", [])
        for item in cities:
            code = item["code"]
            name = item["name"]

            utils.addMenuItem(handle, name, plugin.url_for(ShowRadios, countrycode, code), "flags", code, fanart="background.png")

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle, True)


@plugin.route("/worldradio/showradios/<countrycode>/<citycode>")
def ShowRadios(countrycode, citycode):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, "radio")

    lstItem = GetCountryCities(countrycode)
    countries = lstItem.get("countries", [])
    
    if countries:
        cities = countries[0].get("places", [])
        lstItem = GetItems(citycode, cities)

        for item in lstItem:
            code = item["code"]
            name = item["title"]
            url = item["url"]

            utils.addMenuItemAudio(handle, name, url, "flags", code, fanart="background.png")

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle, True)


#def CreateListItems(name, listitems: List[M3UItem]):
#    handle = plugin.handle
#    xbmcplugin.setPluginCategory(handle, name)
#    xbmcplugin.setContent(handle, "radios")

#    imagedir = ""
#    for item in listitems:
#        utils.addMenuItemVideoM3U(handle, item)

#    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
#    xbmcplugin.endOfDirectory(handle)


def GetItems(code, lstItem):
    lstItem = [x for x in lstItem if x["code"] == code][0].get("channels", [])
    return lstItem


def GetLists():
    strJson = ""

    try:
        strJson = utils.decompressFile(fileName, _name)
        strJson = json.loads(strJson)
    except Exception as e:
        strJson = ""
        logger.error("GetLists error:", e)

    if strJson == "":
        utils.MessageNotification(config.getString(30148))

    return strJson

def GetCountryCities(code):
    strJson = ""
    fileName = f"{code}.bin"
    try:
        strJson = utils.decompressFile(fileName, _name, True)
        strJson = json.loads(strJson)
    except Exception as e:
        strJson = ""
        logger.error("GetLists error:", e)

    if strJson == "":
        utils.MessageNotification(config.getString(30148))

    return strJson


plugin.run()
