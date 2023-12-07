# Module: WorldLiveTV
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

TEMP_LISTFILE_NAME = "~temp.dat"

_name = "WorldTv"
fileName = f"list{_name}.bin"
plugin = routing.Plugin()

jsonIcons = json.loads('{' \
' "AFR"    : "africa",      ' \
' "AMER"   : "northamerica",' \
' "ARAB"   : "asia",        ' \
' "ASIA"   : "asia",        ' \
' "APAC"   : "asia",        ' \
' "CARIB"  : "northamerica",' \
' "CAS"    : "asia",        ' \
' "CIS"    : "asia",        ' \
' "EUR"    : "europe",      ' \
' "EMEA"   : "europe",      ' \
' "HISPAM" : "southamerica",' \
' "LATAM"  : "southamerica",' \
' "LAC"    : "southamerica",' \
' "MAGHREB": "africa",      ' \
' "MIDEAST": "asia",        ' \
' "MENA"   : "africa",      ' \
' "NORD"   : "europe",      ' \
' "NORAM"  : "northamerica",' \
' "NAM"    : "northamerica",' \
' "OCE"    : "oceania",     ' \
' "SAS"    : "asia",        ' \
' "SSA"    : "africa",      ' \
' "WAFR"   : "africa",      ' \
' "INT"    : "international"' \
'}')


@plugin.route("/worldtv")
def Start():
    ShowContinentsList()


def ShowContinentsList():
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, config.getString(30126))

    lstItem = GetLists()
    if not lstItem:
        return

    for item in lstItem.get("worlditems", {}):
        name = item["name"]
        code = item["code"]

        #if code == "INT": continue
        utils.addMenuItem(handle, name, plugin.url_for(ShowCountries, code), "world", jsonIcons.get(code, ""))

    xbmcplugin.endOfDirectory(handle)


@plugin.route("/worldtv/showcountries/<continentcode>")
def ShowCountries(continentcode):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, continentcode)

    lstItem = GetLists()
    lstItem = GetItems(continentcode, lstItem)
    for item in lstItem.get("worlditems", {}):
        code = item["code"]
        name = item["name"]
        url = item["url"]

        if code == "it":
            continue

        utils.addMenuItem(handle, name, plugin.url_for(SwitchList, name, url), "flags", code, fanart="background.png")

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle, True)


@plugin.route("/worldtv/switchlist/<name>/<code>")
def SwitchList(name, code):
    handle = plugin.handle
    url = utils.fromBase64(code)

    if handle == -1:
        utils.setListInt(name, url, "")
    else:
        m3u = M3UParser(logger)
        m3u.exclusion = []
        m3u.loadM3U(url, utils.getPersonalPathFile(TEMP_LISTFILE_NAME))

        CreateListItems(name, m3u.getItems(M3UStreamType.LIVE))


def CreateListItems(name, listitems: List[M3UItem]):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, name)
    xbmcplugin.setContent(handle, "videos")

    imagedir = ""
    for item in listitems:
        utils.addMenuItemVideoM3U(handle, item)

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


plugin.run()
