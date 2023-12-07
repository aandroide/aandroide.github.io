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
from lib import logger, config, utils, customlist
from lib.m3u.m3uitem import M3UItem
from lib.m3u.m3ulist import M3UList
from lib.m3u.m3uparser import M3UParser, M3UStreamType

TEMP_LISTFILE_NAME = "~temp.dat"

_name = "WorldLiveTvLists"
fileName = f"list{_name}.bin"
plugin = routing.Plugin()


@plugin.route("/wltvlist")
def Start():
    ShowLists()


def ShowLists():
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, "Internal")

    lstItem: List[customlist.CustomList]
    lstItem = GetLists()
    if not lstItem:
        return

    for item in lstItem:
        name = item.Name
        code = item.Id

        utils.addMenuItem(handle, name, plugin.url_for(SwitchList, code))

    xbmcplugin.endOfDirectory(handle)


@plugin.route("/wltvlist/<code>")
def SwitchList(code):
    handle = plugin.handle

    lstItem: List[customlist.CustomList]
    lstItem = GetLists()
    if not lstItem:
        return

    selectedList = ""
    for item in lstItem:
        if item.Id == code:
            selectedList = item
            break

    if selectedList:
        m3uList = selectedList.Lists[0]
        m3uList.List = utils.getOnlineOrLocalCacheLink(utils.computeListUrl(selectedList))
        m3uList.Epg  = utils.EPG_URL
        m3u = M3UParser(logger)
        m3u.loadM3U(m3uList.List, utils.getPersonalPathFile(TEMP_LISTFILE_NAME))

        CreateListItems(selectedList.Name, m3u.getItems(M3UStreamType.LIVE))


def CreateListItems(name, listitems: List[M3UItem]):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, name)
    xbmcplugin.setContent(handle, "videos")

    imagedir = ""
    for item in listitems:
        item.Title = f"[{item.TvgChNo}] - {item.Title}" 
        utils.addMenuItemVideoM3U(handle, item)

    #xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle)


def GetItems(code, lstItem):
    lstItem = [x for x in lstItem.get("worlditems", {}) if x["code"] == code][0]
    return lstItem


def GetLists():
    strJson = ""

    try:
        strJson = utils.getRemoteLists()
    except Exception as e:
        strJson = ""
        logger.error("GetLists error:", e)

    if strJson == "":
        utils.MessageNotification(config.getString(30148))

    return strJson


plugin.run()
