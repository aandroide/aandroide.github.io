# Module: VodManager
# Author: CrAcK75
# Created on: 06/05/2021
#

import xbmc
import xbmcgui
import xbmcplugin
import routing
import os

from typing import List
from lib import logger, config, utils, listmanager
from lib.m3u import m3uparser
from lib.m3u.m3ulist import M3UList
from lib.m3u.m3uitem import M3UItem
from lib.m3u.m3uparser import M3USearchType, M3UStreamType, M3UStreamSubGroup

STEP_YEARS_GROUP = 3

showPosters = config.getSetting("showVODPosters")

plugin = routing.Plugin()

@plugin.route("/vodmanager")
def Start():
    ShowUserLists()


def ShowUserLists():
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, config.getString(30150))
    xbmcplugin.setContent(handle, "files")

    lstItem = getLists()
    if not lstItem:
        utils.MessageNotification(config.getString(30158), 10)

        return

    for item in lstItem:
        if item.Id:
            utils.addMenuItem(handle,item.Name,plugin.url_for(ShowChoice, item.Id),"list","list.png")

    if lstItem:
        utils.addMenuItem(handle,config.getString(30151),plugin.url_for(GlobalSearch, None),"search","search.png") #GlobalSearch

    xbmcplugin.endOfDirectory(handle)


@plugin.route("/vodmanager/globalsearch/<streamType>")
def GlobalSearch(streamType):
    handle = plugin.handle
    
    content = "videos"
    xbmcplugin.setPluginCategory(handle, config.getString(30151)) #GlobalSearch
    xbmcplugin.setContent(handle, content)

    utils.addMenuItem(handle, config.getString(30152), plugin.url_for(ShowSearch, None, M3UStreamType.MOVIES), "list", "list.png") #Film
    utils.addMenuItem(handle, config.getString(30153), plugin.url_for(ShowSearch, None, M3UStreamType.SERIES), "list", "list.png") #SerieTV

    xbmcplugin.endOfDirectory(handle)


@plugin.route("/vodmanager/showchoice/<itemId>") 
@plugin.route("/vodmanager/showchoice/<itemId>/<streamType>") 
def ShowChoice(itemId, streamType: M3UStreamType = None):
    handle = plugin.handle
    
    if streamType and isinstance(streamType, str):
        streamType = M3UStreamType[streamType]

    item = getM3UListItem(itemId)
    content = "videos"
    if not streamType:
        xbmcplugin.setPluginCategory(handle, item.Name)
    else:
        xbmcplugin.setPluginCategory(handle, "{} / {}".format(item.Name, str(streamType)))
        content = "movies" if streamType == M3UStreamType.MOVIES else "tvshows"

    xbmcplugin.setContent(handle, content)

    if(not streamType):
        utils.addMenuItem(handle, config.getString(30152), plugin.url_for(ShowChoice, itemId, M3UStreamType.MOVIES), "list", "list.png") #30152 = Film 
        utils.addMenuItem(handle, config.getString(30153), plugin.url_for(ShowChoice, itemId, M3UStreamType.SERIES), "list", "list.png") #30153 = SerieTV
    else:
        utils.addMenuItem(handle, config.getString(30154), plugin.url_for(ShowGroups, itemId, streamType, M3UStreamSubGroup.ABC  , M3USearchType.StartsWith), "list", "list.png") #A-B-C
        utils.addMenuItem(handle, config.getString(30155), plugin.url_for(ShowGroups, itemId, streamType, M3UStreamSubGroup.GROUP, M3USearchType.StartsWith), "list", "list.png") #Gruppi
        utils.addMenuItem(handle, config.getString(30179), plugin.url_for(ShowGroups, itemId, streamType, M3UStreamSubGroup.YEAR,  M3USearchType.Equals),         "list", "list.png") #Anno
        utils.addMenuItem(handle, config.getString(30180), plugin.url_for(ShowGroups, itemId, streamType, M3UStreamSubGroup.GENRE, M3USearchType.ContainsInList), "list", "list.png") #Genere
        utils.addMenuItem(handle, config.getString(30156), plugin.url_for(ShowSearch, itemId, streamType), "list", "list.png") #Ricerca

    xbmcplugin.endOfDirectory(handle)


@plugin.route("/vodmanager/showgroups/<itemId>/<streamType>/<subGroup>/<searchType>")
@plugin.route("/vodmanager/showgroups/<itemId>/<streamType>/<subGroup>/<searchType>/<txtSearch>")
def ShowGroups(itemId, streamType: M3UStreamType, subGroup: M3UStreamSubGroup, searchType: M3USearchType, txtSearch = ""):
    handle = plugin.handle
    txtSearch = utils.fromBase64(txtSearch)

    if isinstance(streamType, str):
        streamType = M3UStreamType[streamType]
    if isinstance(subGroup, str):
        subGroup   = M3UStreamSubGroup[subGroup]
    if isinstance(searchType, str):
        searchType = M3USearchType[searchType]

    item = getM3UListItem(itemId)
    name = "{} / {} / {}".format(item.Name, str(streamType), str(subGroup))
    xbmcplugin.setPluginCategory(handle, name)
    content = "movies" if streamType == M3UStreamType.MOVIES else "tvshows"
    xbmcplugin.setContent(handle, content)

    lstGroup = list()
    if item != None:
        if(subGroup == M3UStreamSubGroup.ABC):
            lstGroup = getAlphabeticGroups()
        elif(subGroup == M3UStreamSubGroup.GROUP):
            lstGroup = listmanager.getUserListGroup(item, streamType, True, searchType, txtSearch)
        elif(subGroup == M3UStreamSubGroup.YEAR):
            lstGroup = getYearsGroups()
        elif(subGroup == M3UStreamSubGroup.GENRE):
            lstGroup = listmanager.getUserListGenre(item, streamType, txtSearch)

        if lstGroup:
            createGroupItems(itemId, name, streamType, subGroup, lstGroup)
        else:
            utils.MessageNotification(config.getString(30157))
    else:
        xbmcplugin.endOfDirectory(handle)


@plugin.route("/vodmanager/showsearch/<itemId>/<streamType>")
def ShowSearch(itemId, streamType: M3UStreamType):
    handle = plugin.handle
    isGlobalSearch = (not itemId or itemId == 'None')
    
    if isinstance(streamType, str):
        streamType = M3UStreamType[streamType]

    subGroup = M3UStreamSubGroup.SEARCH
    #if streamType == M3UStreamType.MOVIES:
    #    subGroup = M3UStreamSubGroup.ABC
    #elif streamType == M3UStreamType.SERIES:
    #    subGroup = M3UStreamSubGroup.SEARCH
    txtSearch = str(config.getSetting(f"VOD_Search_{streamType}"))
    txtSearch = xbmcgui.Dialog().input(f"{config.getString(30156)}: {streamType}", txtSearch, type = xbmcgui.INPUT_ALPHANUM) #Search MOVIE:

    if txtSearch:
        config.setSetting(f"VOD_Search_{streamType}", txtSearch)

        ShowFiltered(itemId, streamType, subGroup, utils.toBase64(txtSearch), isUserSearch=True)

        #if streamType == M3UStreamType.MOVIES:
        #    ShowFiltered(itemId, streamType, subGroup, utils.toBase64(txtSearch), isUserSearch=True)
        #elif streamType == M3UStreamType.SERIES:
        #    ShowFiltered(itemId, streamType, M3UStreamSubGroup.ABC, utils.toBase64(txtSearch), isUserSearch=True)

        #    if isGlobalSearch:
        #        ShowFiltered(itemId, streamType, subGroup, utils.toBase64(txtSearch), isUserSearch=True)
        #    else:
        #        item = getM3UListItem(itemId)
        #        name = "{} / {} / {}".format(item.Name, str(streamType), str(subGroup))
        #        lstGroup = listmanager.getUserListGroup(item, streamType, True, M3USearchType.Contains, txtSearch)
        #        createGroupItems(itemId, name, streamType, subGroup, lstGroup)
    #else:
    #    return

    xbmcplugin.endOfDirectory(handle)


@plugin.route("/vodmanager/showfiltered/<itemId>/<streamType>/<subGroup>/<txtSearch>/<isUserSearch>")
def ShowFiltered(itemId, streamType: M3UStreamType, subGroup: M3UStreamSubGroup, txtSearch: str, isUserSearch: bool):
    handle = plugin.handle
    txtSearch = utils.fromBase64(txtSearch)
    if isinstance(streamType, str):
        streamType = M3UStreamType[streamType]
    if isinstance(subGroup, str):
        subGroup   = M3UStreamSubGroup[subGroup]

    isUserSearch = True if str(isUserSearch).lower() == "true" else False
    isGlobalSearch = (not itemId or itemId == 'None')
    lstItems = list()
    name = ""

    if not isGlobalSearch:
        item = getM3UListItem(itemId)
        lstItems = [item]
        name = "{} / {} / {}".format(item.Name, str(streamType), txtSearch)
    else:
        lstItems = getLists()
        name = "{} / {}".format(config.getString(30151), txtSearch) #GlobalSearch

    xbmcplugin.setPluginCategory(handle, name)
    
    content = "files" 
    if streamType == M3UStreamType.MOVIES:
       content = "movies" 
    elif streamType == M3UStreamType.SERIES:
       content = "episodes"

    xbmcplugin.setContent(handle, content)

    if lstItems:
        lstVod = list()
        res: List[M3UItem]

        if isGlobalSearch:
            for item in lstItems:
                res = listmanager.getUserListStreams(item, streamType, M3UStreamSubGroup.SEARCH, txtSearch, isUserSearch)
                for x in res: x.Title = f"{x.Title} [{item.Name}]"
                lstVod.extend(res)
        else:
            lstVod.extend(listmanager.getUserListStreams(lstItems[0], streamType, subGroup, txtSearch, isUserSearch))
        
        if lstVod:
            createListItems(name, content, lstVod)
        else:
            utils.MessageNotification(config.getString(30157))
    else:
        xbmcplugin.endOfDirectory(handle)

    exit()


def createGroupItems(itemId, name, streamType: M3UStreamType, subGroup: M3UStreamSubGroup, listGroups: list()):
    handle = plugin.handle
    xbmcplugin.setPluginCategory(handle, name)

    for groupName in listGroups:
        if(not groupName): 
            displayGroup = "[Unknown]"
        else:
            displayGroup = groupName

        if(not groupName or groupName == "#"): 
            groupName = m3uparser.NOT_DIGIT_OR_NUMERIC

        groupName = utils.toBase64(groupName)
        if streamType == M3UStreamType.SERIES and subGroup == M3UStreamSubGroup.ABC:
            #show serie group startwith selected letter
            utils.addMenuItem(handle, displayGroup, plugin.url_for(ShowGroups, itemId, streamType, M3UStreamSubGroup.GROUP, M3USearchType.StartsWith, groupName), "list", "list.png")
        elif streamType == M3UStreamType.SERIES:
            utils.addMenuItem(handle, displayGroup, plugin.url_for(ShowFiltered, itemId, streamType, subGroup, groupName, True),  "list", "list.png")
        else:
            utils.addMenuItem(handle, displayGroup, plugin.url_for(ShowFiltered, itemId, streamType, subGroup, groupName, False), "list", "list.png")
    if subGroup == M3UStreamSubGroup.YEAR:
        xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_NONE) #SORT_METHOD_UNSORTED 
    else:
        xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle)

def createListItems(name, content, listItems: List[M3UItem]):
    handle = plugin.handle

    xbmcplugin.setPluginCategory(handle, name)
    imagedir = ""
    for item in listItems:
        url = item.Link
        isFolder = "plugin" in url and item.IsSerie

        logo = item.TvgLogo
        if not isFolder:
            #logo = item.TvgLogo
            if not showPosters:
                logo = "movie.png" if item.IsFilm else "tvshow.png"
                logo = os.path.join(config.ADDON_PATH, "resources", logo)
        
        utils.addMenuItemPlayable(handle, item.Title, url, plot = "", icon = "", thumb = logo, poster = logo, fanart = logo, genre = item.TvgGenres, year = item.TvgYear, mediatype = "video", isFolder = isFolder)

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle)


def getAlphabeticGroups():
    res = list()
    string = "#" + m3uparser.ABC.upper()
    res[:0]=string

    return res

def getYearsGroups():
    from datetime import date
    res = list()

    for y in reversed(range(2011, date.today().year+1)):
        res.append(f"{y}")
    for y in reversed(range(1990, 2011, STEP_YEARS_GROUP)):
        res.append(f"{y} - {y + STEP_YEARS_GROUP - 1}")
    res.append("1900 - 1989")

    return res

def getLists() -> List[M3UList]:
    res = list()
    settingsCustomLists = listmanager.getSettingsCustomLists(utils.PARAM_USER_LIST_NAME)

    for item in settingsCustomLists:
        res.extend(item.Lists)

    return res

def getM3UListItem(listId) -> M3UList:
    return next((_item for _item in getLists() if _item.Id == listId), None)

plugin.run()
