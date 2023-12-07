# -*- coding: utf-8 -*-
# Module: WorldLiveTV
# Author: CrAcK75
# Created on: 01/02/2022
#

import os
import re
import sys
import random
import json
from urllib import request
from enum import Enum
from lib import logger
from lib.m3u.m3uitem import M3UItem

NOT_DIGIT_OR_NUMERIC = "[UNK]"
ALL_GROUPS_SELECTED = "*"
ABC="abcdefghijklmnopqrstuvwxyz"

TAG_TVG_NAME = "tvg-name"
TAG_TVG_CHNO = "tvg-chno"
TAG_TVG_ID   = "tvg-id"
TAG_TVG_LOGO = "tvg-logo"
TAG_GROUP_TITLE = "group-title"


class M3UStreamType(Enum):
    ALL    = 0
    LIVE   = 1
    MOVIES = 2
    SERIES = 3
    KARAOKE= 4

    def __str__(self):
        return self.name

class M3UStreamSubGroup(Enum):
    ABC   = 0
    GROUP = 1
    YEAR  = 2
    GENRE = 3
    SEARCH= 4

    def __str__(self):
        return self.name

class M3USearchField(Enum):
    Title     = 1
    TvgName   = 2
    TvgChNo   = 3
    TvgId     = 4
    TvgLogo   = 5
    TvgGroup  = 6
    TvgYear   = 7
    TvgGenres = 8
    Link      = 9

    def __str__(self):
        return self.name

class M3USearchType(Enum):
    Equals     = 0
    StartsWith = 1
    EndsWith   = 2
    Contains   = 3
    ContainsInList = 4

    def __str__(self):
        return self.name

class M3UParser:
    exclusion = list()
    exclusionNamesStartsWith = list()
    groupsFilter = list()
    lstGroupCleanup = list()
    isValid = False

    def __init__(self, logging):
        self.lines     = list()
        self.items     = list()
        self.selection = list()
        self.logging   = logging

    # Load the file from the given url
    def loadM3U(self, url, filename):
        currentDir = os.path.dirname(os.path.realpath(__file__))
        if not filename:
            filename = "~~temp.dat"

        try:
            filename = os.path.join(currentDir, filename)
            request.urlretrieve(url, filename)
            self.readM3U(filename)
        except Exception as ex:
            logger.error("Cannot download anything from the provided url")
            logger.error(ex)

    # Read the file from the given path
    def readM3U(self, filename):
        self.filename = filename
        self.__parseFile()

    # Read all file lines
    def __parseFile(self):
        self.items = list()

        fileContent = None

        try:
            fileContent = open(self.filename, encoding="utf8")

            if fileContent:
                strFileContentLines = fileContent.read()

                if strFileContentLines[:7].lower() == "#extm3u":
                    fileContent.seek(0, 0)
                    self.lines = [ line.rstrip("\n") for line in fileContent ]
                    self.__manageLines()
                else:
                    jsonData = json.loads(strFileContentLines)
                    self.items = [ M3UItem.from_dict(D) for D in jsonData ]
                    self.selection = self.items
                self.isValid = True
            else:
                logger.error(f"No file content in provided file: {self.filename}")
        except Exception as ex :
            logger.error(ex)
            self.items = list()

        self.lines = list()

    def __manageLines(self):
        linesCount = len(self.lines)

        n = 0
        while n < linesCount - 1:
            n += 1
                
            currentLine = self.lines[n]
            if currentLine.strip() != "" and currentLine[0] == "#":
                lineInfo  = ""
                lineLink  = ""
                userAgent = ""
                referer   = ""

                while (not (lineLink.lower().startswith("http") or lineLink.lower().startswith("plugin"))) and n < linesCount - 1:
                    currentLine = self.lines[n]

                    if currentLine and currentLine[0].startswith("#"):
                        if currentLine.lower().startswith("#extvlcopt"):
                            if "user-agent" in currentLine.lower():
                                userAgent = currentLine.split("=")[1]
                            if "referrer" in currentLine.lower() or "referer" in currentLine.lower():
                                referer = currentLine.split("=")[1]
                        if currentLine.lower().startswith("#extinf"):
                            lineInfo = currentLine
                        n += 1
                        continue
                    elif currentLine.lower().startswith("http") or currentLine.lower().startswith("plugin"):
                        lineLink = currentLine
                    else:
                        n += 1
                        continue

                    if lineLink:
                        for x in self.exclusion: 
                            if x in lineLink: break

                    if lineInfo and lineLink:
                        try:
                            item: M3UItem
                            item = M3UItem.from_extinf_url(lineInfo, lineLink)

                            if item and item.IsValid():
                                if userAgent and not item.UserAgent:
                                    item.UserAgent = userAgent
                                if referer and not item.Referer:
                                    item.Referer = referer
                            
                                self.items.append(item) 

                        except Exception as ex :
                                logger.error(ex)
                                logger.error(lineInfo)
                                logger.error(lineLink)


    def saveM3U(self, fileName):
        lines = list()
        lines.append("#EXTM3U")
        lines.append("")

        for x in self.selection:
            group = x.TvgGroup if x.TvgGroup else "[Unknown]"
            link  = x.Link if x.Link else "https://foo_.com"

            if x.TvgChNo == 0:
                lines.append(f'#EXTINF:-1 tvg-id="{x.TvgId}" tvg-name="{x.TvgName}" tvg-logo="{x.TvgLogo}" group-title="{group}",{x.Title}')
            else:
                lines.append(f'#EXTINF:-1 tvg-chno="{x.TvgChNo}" tvg-id="{x.TvgId}" tvg-name="{x.TvgName}" tvg-logo="{x.TvgLogo}" group-title="{group}",{x.Title}')

            lines.append(link)

        with open(fileName, "w", encoding="utf8") as f:
            f.write('\n'.join(lines))

    def saveM3UJ(self, fileName):
        with open(fileName, "w", encoding="utf8") as f:
            f.write(json.dumps(self.selection, default = lambda x: x.__dict__))

    # Get selected type channels of the list (98% of server panels list)
    def getItems(self, streamType: M3UStreamType, searchField: M3USearchField = None, searchType: M3USearchType = None, search = "") -> list:
        self.selection = list()

        if streamType == M3UStreamType.ALL: 
            self.selection = self.items
        # Get only live channel of the list (98% of server panels list)
        elif streamType == M3UStreamType.LIVE: 
            self.selection = list(filter(lambda item: item.IsLive, self.items))
        
        # Get only Film VOD of the list (98% of server panels list)
        elif streamType == M3UStreamType.MOVIES: 
            self.selection = list(filter(lambda item: item.IsFilm, self.items))
        
        # Get only SeriesTV VOD of the list (98% of server panels list)
        elif streamType == M3UStreamType.SERIES: 
            self.selection = list(filter(lambda item: item.IsSerie, self.items))

        # Get only Karaoke VOD of the list 
        elif streamType == M3UStreamType.KARAOKE: 
            self.selection = list(filter(lambda item: item.IsKaraoke, self.items))

        if search and searchField != None:
            fieldOfSearch = str(searchField)
            if (search == NOT_DIGIT_OR_NUMERIC.lower()):
                if(searchField == M3USearchField.TvgGroup):
                    search = ""
                elif(searchField == M3USearchField.TvgName):
                    search = list()
                    search[:0]=ABC
                    self.selection = list(filter(lambda item: not item.TvgName.lower().startswith(tuple(search)), self.selection))
            else:
                if not isinstance(search, list):
                    search = [search]
                    search = [x.lower() for x in search]
                
                if searchType == M3USearchType.Equals:
                    res = []
                    for item in self.selection:
                        if str(item.__dict__.get(fieldOfSearch, "")).lower() in search:
                            res.append(item)
                    self.selection = res
                elif searchType == M3USearchType.StartsWith:
                    self.selection = list(filter(lambda item: item.__dict__.get(fieldOfSearch, "").lower().startswith(tuple(search)), self.selection))
                elif searchType == M3USearchType.EndsWith:
                    self.selection = list(filter(lambda item: item.__dict__.get(fieldOfSearch, "").lower().endswith(tuple(search)), self.selection))
                elif searchType == M3USearchType.Contains:
                    self.selection = list(filter(lambda item: all(f in str(item.__dict__.get(fieldOfSearch, "")).lower() for f in search), self.selection))
                elif searchType == M3USearchType.ContainsInList:
                    self.selection = list(filter(lambda item: all(f in list(map(lambda x: x.lower(), item.__dict__.get(fieldOfSearch, []))) for f in search), self.selection))

        if not self.allGroupsSelected():
            self.selection = list(filter(lambda item: item.TvgGroup in self.groupsFilter, self.selection))

        return self.selection

    def allGroupsSelected(self):
        return self.groupsFilter == [ALL_GROUPS_SELECTED] or self.groupsFilter == []

    # Getter for the groups
    def getGroups(self, streamType: M3UStreamType, filterGroups=[]) -> list:
        res = list()

        for item in self.getItems(streamType):
            g = item.TvgGroup

            if (g not in res):
                if(filterGroups and g in filterGroups) or (not filterGroups):
                    res.append(g)

        res.sort()
        return res

    def getGenres(self, streamType: M3UStreamType) -> list:
        res = list()

        for item in self.getItems(streamType):
            lstGenres = item.TvgGenres

            for g in lstGenres:
                if (g not in res):
                    res.append(g)

        res.sort()
        return res


    def excludeStubs(self, field:str, lstCleanup: list = []):
        self.items = list(filter(lambda item: not item.__dict__.get(field, "").lower().startswith(tuple(lstCleanup)), self.items))

    def cleanUpGroups(self, lstCleanup: list = []):
        for idx in range(len(self.items)):
            for x in lstCleanup:
                #self.items[idx].TvgGroup = re.sub(f"^{x}", "", self.items[idx].TvgGroup, flags=re.IGNORECASE).strip().strip("-").strip()
                self.items[idx].TvgGroup = re.sub(x, "", self.items[idx].TvgGroup, flags=re.IGNORECASE).strip().strip("-").strip()

    def cleanUpGroupsStartsWith(self, lstCleanup: list = []):
        for idx in range(len(self.items)):
            for x in lstCleanup:
                if bool(re.match(x, self.items[idx].TvgGroup, re.I)):
                    self.items[idx].TvgGroup = self.items[idx].TvgGroup[len(x):].strip().strip("-").strip()

    # Get only live channel of the list (98% of server panels list)
    def getLive(self) -> list:
        return self.getItems(M3UStreamType.LIVE)

    # Get only Film VOD of the list (98% of server panels list)
    def getFilms(self) -> list:
        return self.getItems(M3UStreamType.MOVIES)

    # Get only SeriesTV VOD of the list (98% of server panels list)
    def getSeries(self) -> list:
        return self.getItems(M3UStreamType.SERIES)

    # Get only Karaoke VOD of the list
    def getKaraoke(self) -> list:
        return self.getItems(M3UStreamType.KARAOKE)

    # Get only SerieTV VOD of a group
    def getSerieFromGroup(self, groupName) -> list:
        return self.getItems(M3UStreamType.SERIES, M3USearchField.TvgGroup, M3USearchType.Equals, groupName)

    # Get only Films VOD starting with alpha
    def getFilmFromGroup(self, groupName) -> list:
        return self.getItems(M3UStreamType.MOVIES, M3USearchField.TvgGroup, M3USearchType.Equals, groupName)

    # Get only Karaoke VOD starting with alpha
    def getKaraokeFromGroup(self, groupName) -> list:
        return self.getItems(M3UStreamType.KARAOKE, M3USearchField.TvgGroup, M3USearchType.Equals, groupName)
