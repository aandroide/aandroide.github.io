# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import sys

from typing import List
from lib.customlist import CustomList, ListType
from lib import config, install, utils, listmanager, logger, const
from lib.m3u.m3ulist import M3UList

LIST = 1
CLOSE = 2
SETTING = 3
LEFT = 1
RIGHT = 2
UP = 3
DOWN = 4
EXIT = 10
BACKSPACE = 92

isServerOnLine = utils.checkServerOnLine()
isSimpleInstalled = install.installPvr()
lstList: List[CustomList]
lstList = []


class ListSelection(xbmcgui.WindowXMLDialog):
    def start(self):
        self.preselected = config.getSetting(const.SELECTED_LIST)
        self.list = []
        self.doModal()

    def onInit(self):
        self.selected = 0
        self.preselected = config.getSetting(const.SELECTED_LIST)
        self.List = self.getControl(LIST)

        for item in lstList:
            listItem = xbmcgui.ListItem(item.Name)
            listItem.setProperty("ListType", str(item.TypeOfList))
            
            if self.preselected == item.Id:
                listItem.setArt({"icon": "selected.png"})
                self.selected = True
            else:
                listItem.setArt({"icon": "unselected.png"})
            self.list.append(listItem)

        self.List.reset()
        self.List.addItems(self.list)
        self.setFocusId(LIST)
        self.List.selectItem(self.selected)


    def onClick(self, control):
        selection = self.List.getSelectedPosition()
        selectedList: M3UList
        selectedList = lstList[selection]

        if control == LIST:
            m3uList: M3UList
            m3uList = M3UList()
            if selectedList.TypeOfList == ListType.Emergency:
                m3uList = selectedList.Lists[0]

            elif selectedList.TypeOfList == ListType.Official:
                m3uList = selectedList.Lists[0]
                m3uList.List = utils.getOnlineOrLocalCacheLink(utils.computeListUrl(selectedList))
                m3uList.Epg  = utils.EPG_URL
            
            elif selectedList.TypeOfList == ListType.User:
                m3uList = selectedList.Lists[0]
                m3uList.List = listmanager.getUserListFileLive(m3uList)

            elif selectedList.TypeOfList == ListType.Personal:
                m3uList.Id = selectedList.Id
                m3uList.List = utils.getOnlineOrLocalCacheLink(utils.computeListUrl(selectedList))
                m3uList.Epg = utils.EPG_URL

            if not m3uList.List:
                utils.MessageBox(config.getString(30147))
            else:
                utils.setList(m3uList, not isServerOnLine)
                if isServerOnLine:
                    config.setSetting(const.LAST_SELECTED_ONLINE_LIST, m3uList.Id)

            self.exit()
        elif control == CLOSE:
            self.exit()
        elif control == SETTING:
            config.ADDON.openSettings()


    def onAction(self, action):
        action = action.getId()
        if action in [EXIT, BACKSPACE, LEFT]:
            self.exit()


    def exit(self):
        self.close()


def SetEmergencyList():
    emr = M3UList.from_dict(utils.getEmergencyDTTFtaList()[0])
    utils.setList(emr)


def launch():
    if not isSimpleInstalled:
        return

    if not isServerOnLine:
        utils.MessageBox(30146)

    addonpath = config.ADDON_PATH
    global lstList
    lstList = utils.getRemoteLists() if not config.getSetting("hide_default_list") else []

    lstListPersonal = listmanager.getPersonalLists()

    if lstListPersonal:
        lstList.extend(lstListPersonal)
    
    ListSelection("ListSelection.xml", addonpath, "Default").start()


launch()
