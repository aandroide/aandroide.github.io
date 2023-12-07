# -*- coding: utf-8 -*-
# Module: VodManager
# Author: CrAcK75
# Created on: 06/05/2021

#from ntpath import join
import xbmc, xbmcgui, xbmcvfs, os, json

from enum import Enum
from typing import List
from lib import logger, utils, config, customlist
from lib.m3u.m3ulist import M3UList
from lib.m3u.m3uparser import M3UParser, M3UStreamType, M3UStreamSubGroup, M3USearchField, M3USearchType
from lib.customlist import CustomList

from urllib import request

USERNAME_SUBDIR = "UserList"
GROUPS_CLEANUP = ["\|it\|", "italy vod"]
GROUPS_CLEANUP_STARTS = ["serie tv", "series", "serie",]
TITLES_STUB_EXCLUSION = ["// ", "--", "**", "==", u"\u2023\u2023", u"\u2022\u2022"] 
ALL_GROUPS_SELECTED = "*"

class FileType(Enum):
    ALL    = 0
    Full   = 1
    FullJ  = 2
    Groups = 3
    StreamType = 4
    Live   = 5
    Movies = 6
    Series = 7
    
    def __str__(self):
        return self.name

def checkUserListFile(inputList: M3UList):
    _file = f"~{inputList.Id}_{FileType.Full}.dat"
    _fileFullPath = utils.getPersonalPathFile(_file)

    return utils.checkFileExists(_fileFullPath)

def getUserListFile(inputList: M3UList, forceRefresh: bool = False):
    _fileJFullPath = ""

    _file = f"~{inputList.Id}_{FileType.Full}.dat"
    _fileFullPath = utils.getPersonalPathFile(_file)

    progress = xbmcgui.DialogProgress()
    progress.create(f"{inputList.DisplayName} {config.getString(30160)}", config.getString(30161)) #progress.create(f"{inputList.DisplayName} file info download", "Downloading, please wait...")

    if(utils.localFileNeedsUpdate(_fileFullPath)):
        res = True
        if not forceRefresh:
            res = utils.MessageBoxQuestion(config.getString(30181).format(inputList.DisplayName))
            if not res:
                res = not utils.refreshFileDate(_fileFullPath)
            
        if res:
            progress.update(30, config.getString(30162)) # "Local file needs update..."
            #if(checkUrlExists(inputList.List)): #some provider block head get
            if(inputList.List.startswith("http")):
                try:
                    opener = request.URLopener()
                    headers = utils.getBrowserHeaders()
                    for item in headers: opener.addheader(item, headers[item])
                    opener.retrieve(inputList.List, _fileFullPath)
                    #progress.update(50, config.getString(30163)) #"Local file updated..."
                except Exception as ex:
                    logger.error(f"Error during first attempt getUserListFile: [{ex}]")
                    logger.error("Try again...")
                    try:
                        utils.downloadFile(inputList.List, _fileFullPath, headers = utils.getBrowserHeaders(), timeout = 40)
                        #progress.update(50, config.getString(30163)) #"Local file updated..."
                    except Exception as ex:
                        logger.error(f"Error during second attempt getUserListFile: [{ex}]")
                        pass

                if utils.checkFileExists(_fileFullPath) and utils.isGzFile(_fileFullPath):
                    utils.decompressGZFile(_fileFullPath, _fileFullPath)

            elif utils.checkFileExists(inputList.List):
                xbmcvfs.copy(inputList.List, _fileFullPath)

    if utils.checkFileExists(_fileFullPath):
        _fileJ = f"~{inputList.Id}_{FileType.FullJ}.dat"
        _fileJFullPath = utils.getPersonalPathFile(_fileJ)
        if(utils.localFileNeedsUpdate(_fileJFullPath)):
            progress.update(70, config.getString(30164)) #"Updating file main info..."
            m3u = M3UParser(logger)
            m3u.readM3U(_fileFullPath)
            m3u.cleanUpGroups(GROUPS_CLEANUP)
            m3u.cleanUpGroupsStartsWith(GROUPS_CLEANUP_STARTS)
            m3u.excludeStubs("Title", TITLES_STUB_EXCLUSION)
            m3u.getItems(M3UStreamType.ALL)

            if m3u.isValid:
                m3u.saveM3UJ(_fileJFullPath)
            else:
                os.remove(_fileFullPath)

    progress.update(100, config.getString(30165)) #"All operation done"
    progress.close()

    return _fileJFullPath


def getUserListGenre(inputList: M3UList, streamType: M3UStreamType, txtSearch = "") -> List[str]:
    res = list()

    if not streamType: 
        return res
    
    _file = f"~{inputList.Id}_{streamType}_genres.dat"
    _fileFullPath = utils.getPersonalPathFile(_file)

    if(utils.localFileNeedsUpdate(_fileFullPath)):
        _fileListFullPath = getUserListFile(inputList)
        if(utils.checkFileExists(_fileListFullPath)):
            m3u = M3UParser(logger)
            m3u.readM3U(_fileListFullPath)
            res = m3u.getGenres(streamType)

            utils.writeFile(_fileFullPath, json.dumps(res))
    else:
        res = json.loads(utils.readFile(_fileFullPath))

    #if(filtered and inputList.Groups):
    #    res = list(filter(lambda item: item in inputList.Groups, res))
    if(txtSearch):
        txtSearch = txtSearch.lower()
        res = [item for item in res if txtSearch in item.lower()] 

    res.sort()

    return res


def getUserListGroup(inputList: M3UList, streamType: M3UStreamType, filtered: bool = False, searchType: M3USearchType = M3USearchType.Contains, txtSearch = "") -> List[str]:
    res = list()

    if not streamType: 
        return res
    
    _file = f"~{inputList.Id}_{streamType}_groups.dat"
    _fileFullPath = utils.getPersonalPathFile(_file)

    if(utils.localFileNeedsUpdate(_fileFullPath)):
        _fileListFullPath = getUserListFile(inputList)
        if(utils.checkFileExists(_fileListFullPath)):
            m3u = M3UParser(logger)
            m3u.readM3U(_fileListFullPath)
            res = m3u.getGroups(streamType)

            utils.writeFile(_fileFullPath, json.dumps(res))
    else:
        res = json.loads(utils.readFile(_fileFullPath))

    if filtered and inputList.Groups:
        if inputList.Groups != [ALL_GROUPS_SELECTED]:
            res = list(filter(lambda item: item in inputList.Groups, res))

    #for x in GROUP_CLEANUP:
    #    res = [ re.sub(f"^{x}", "", item, flags=re.IGNORECASE).strip().strip("-").strip() for item in res ]

    if(txtSearch):
        txtSearch = txtSearch.lower()
        if searchType == M3USearchType.StartsWith:
            from lib.m3u import m3uparser
            if txtSearch == m3uparser.NOT_DIGIT_OR_NUMERIC.lower():
                search = list()
                search[:0] = m3uparser.ABC
                res = list(filter(lambda item: not item.lower().startswith(tuple(search)), res))
            else:
                res = [item for item in res if item.lower().startswith(txtSearch)]
        elif searchType == M3USearchType.Contains:
            res = [item for item in res if txtSearch in item.lower()]

    res.sort()

    return res


def getUserListStreams(inputList: M3UList, streamType: M3UStreamType, subGroup: M3UStreamSubGroup, txtSearch = "", isUserSearch: bool = False):
    streams = list()
    txtSearch = txtSearch.lower()

    _fileListFullPath = getUserListFileStream(inputList, streamType)
    if(utils.checkFileExists(_fileListFullPath)):
        m3u = M3UParser(logger)
        m3u.readM3U(_fileListFullPath)

        searchField = M3USearchField.TvgName 
        if subGroup == M3UStreamSubGroup.ABC: 
            searchField = M3USearchField.TvgName
            searchType = M3USearchType.StartsWith
        elif subGroup == M3UStreamSubGroup.GROUP:
            searchField = M3USearchField.TvgGroup
            searchType = M3USearchType.Equals
        elif subGroup == M3UStreamSubGroup.YEAR:
            searchField = M3USearchField.TvgYear
            searchType = M3USearchType.Equals
            txtSearch = getRangeYearSearch(txtSearch)
        elif subGroup == M3UStreamSubGroup.GENRE:
            searchField = M3USearchField.TvgGenres
            searchType = M3USearchType.ContainsInList
        elif subGroup == M3UStreamSubGroup.SEARCH: 
            searchField = M3USearchField.TvgName
            searchType = M3USearchType.Contains
        
        #searchField = M3USearchField.TvgName if subGroup == M3UStreamSubGroup.ABC else M3USearchField.TvgGroup
        #if isUserSearch:
        #    searchType = M3USearchType.Contains
        #else:
        #    searchType = M3USearchType.StartsWith if searchField == M3USearchField.TvgName else M3USearchType.Equals

        streams = m3u.getItems(streamType, searchField, searchType, txtSearch)
        streams.sort(key=lambda x: x.Title)
    return streams


def getRangeYearSearch(searchText) -> list:
    splitted = []
    splitted = searchText.split("-")
    if len(splitted) == 1:
        splitted.append(splitted[0])
        
    YStart = int(splitted[0].strip())
    YEnd   = int(splitted[1].strip())
    rangeY = []
    for y in range(YStart,YEnd+1): 
        rangeY.append(str(y))

    return rangeY
    

def getUserListFileStream(inputList: M3UList, streamType: M3UStreamType):
    _file = f"~{inputList.Id}_{streamType}.dat"
    _fileFullPath = utils.getPersonalPathFile(_file)

    if(utils.localFileNeedsUpdate(_fileFullPath)):
        _fileListFullPath = getUserListFile(inputList)
        if(utils.checkFileExists(_fileListFullPath)):
            m3u = M3UParser(logger)
            m3u.readM3U(_fileListFullPath)
            m3u.groupsFilter = inputList.Groups
            m3u.getItems(streamType)
            m3u.saveM3UJ(_fileFullPath)
        else:
            _fileFullPath = ""
    
    return _fileFullPath


def getUserListFileLive(inputList: M3UList):
    streamType = M3UStreamType.LIVE
    _file = f"~{inputList.Id}_{streamType}.dat"
    _fileFullPath = utils.getPersonalPathFile(_file)

    if(utils.localFileNeedsUpdate(_fileFullPath)):
        _fileListFullPath = getUserListFile(inputList)
        if(utils.checkFileExists(_fileListFullPath)):
            m3u = M3UParser(logger)
            m3u.readM3U(_fileListFullPath)
            m3u.groupsFilter = inputList.Groups
            m3u.getItems(streamType)
            m3u.saveM3U(_fileFullPath)
    
    if(not utils.checkFileExists(_fileFullPath)):
        _fileFullPath = ""

    return _fileFullPath


def getUserListUrls():
    urlsList = list()
    customLists: List[CustomList]
    userLists: List[M3UList]

    customLists = getSettingsCustomLists(utils.PARAM_USER_LIST_NAME)
    
    xbmc.executebuiltin("ActivateWindow(busydialognocancel)")
    for lst in customLists:
        userLists = lst.Lists
        for l in userLists:
            _fileJ = f"~{l.Id}_{FileType.FullJ}.dat"
            _fileJFullPath = utils.getPersonalPathFile(_fileJ)
            m3u = M3UParser(logger)
            m3u.readM3U(_fileJFullPath)
            items = m3u.getItems(M3UStreamType.ALL)
            listItems = list(filter(lambda item: item.Link.lower().startswith("http"), items))
            _list = list(map(lambda item: "/".join(item.Link.split("/")[2:-1]), listItems))
            _list = list(set(_list))

            urlsList.extend(_list)
    xbmc.executebuiltin("Dialog.Close(busydialognocancel)")
    
    return list(set(urlsList))


def getSettingsCustomLists(settingSectionName: str):
    strSetting = config.getSetting(settingSectionName)
    strSetting = utils.decompressString(strSetting)
    return customlist.CustomListfromjson(strSetting) if strSetting else []


def setSettingsCustomLists(settingSectionName: str, strSetting):
    strSetting = utils.compressString(strSetting)
    config.setSetting(settingSectionName, strSetting)
    

def getPersonalLists() -> List[CustomList]:
    res = list()

    res.extend(getSettingsCustomLists(utils.PARAM_LIST_NAME))
    res.extend(getSettingsCustomLists(utils.PARAM_USER_LIST_NAME))
    
    return res


def getListById(listId) -> M3UList:
    res = getSettingsCustomLists(utils.PARAM_USER_LIST_NAME)

    for x in res:
        if x.Id == listId:
            return x.Lists[0]
    return None


def cleanup(fileType: FileType = FileType.Groups, listId = ""):
    utils.cleanupFiles(f"~{listId}*{fileType}*.dat*")


def deleteList(listId):
    utils.cleanupFiles(f"~{listId}*")

