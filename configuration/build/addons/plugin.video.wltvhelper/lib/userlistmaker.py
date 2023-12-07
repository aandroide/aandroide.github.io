# -*- coding: utf-8 -*-

import xbmcgui, json, copy, inspect, os
import xbmcvfs
import requests
from xbmcvfs import translatePath
from typing import List
from enum import Enum

from lib import config, utils, customlist, listmanager, logger
from lib.customlist import CustomList, ListType
from lib.m3u.m3ulist import M3UList
from lib.m3u.m3ugroupitem import M3UGroupItem
from lib.m3u.m3uparser import M3UStreamType

EXIT = 10
BACKSPACE = 92

MAKER = 100
LIST = 200
GROUPS = 300

BTN_LIST_MOVE_UP = 101
BTN_LIST_MOVE_DOWN = 102
BTN_LIST_GROUPS_CHOOSE = 103
BTN_LIST_GROUPS_RESET = 104
BTN_LIST_DELETE = 105
BTN_LIST_REFRESH = 106

BTN_GROUPS_CHOSEN = 201
BTN_GROUPS_UNSELECT_ALL = 202
BTN_GROUPS_SELECT_ALL = 203

BTN_LIST_BACK = 99  # Left Arrow

TXT_DIALOG_NAME = 1
TXT_DIALOG_LIST = 21
TXT_DIALOG_EPG = 31

BTN_DIALOG_LIST_SEARCH = 22
BTN_DIALOG_EPG_SEARCH = 32

BTN_DIALOG_OK = 41
BTN_DIALOG_CANCEL = 42

ALL_GROUPS_SELECTED = "*"

isServerOnLine = utils.checkServerOnLine()
remoteLists = List[M3UList]
settingsCustomLists = List[CustomList]


class FormMode(Enum):
    List = 0
    UserList = 1
    ImportFromUrl = 2
    ImportFromFile = 3


class PathImportType(Enum):
    Url = 0
    File = 1


class SearchCustomFrom(Enum):
    Settings = 0
    Current = 1


class ListMaker(xbmcgui.WindowXMLDialog):
    mode: FormMode = None

    def start(self, windowType: int, mode: FormMode = None, custom: CustomList = None, listGroupId: str = ""):
        self.mode = mode
        self.windowType = windowType  # integer of MAKER, LIST, GROUPS
        self.customList = custom

        self.Groups = list()
        self.listGroupsId = listGroupId

        self.doModal()

        if self.windowType == GROUPS: return self.Groups
        else: return self.customList

    def onInit(self):
        self.list = list()
        self.List = self.getControl(self.windowType)

        # Main Dialog
        if self.windowType == MAKER:
            for customList in settingsCustomLists:
                item = self.getListItem(customList.Name, customList.Id)
                self.list.append(item)  # Personal Lists

            self.list.append(xbmcgui.ListItem(""))  # Add Button

        # Lists Selector
        elif self.windowType == LIST:
            self.showLists(remoteLists)

        # Groups Selector
        elif self.windowType == GROUPS:
            self.showGroups(self.listGroupsId)

        self.loadList(0)

    def onClick(self, control):
        #logger.debug("Enter in: ", inspect.currentframe().f_code.co_name)
        if control == BTN_LIST_BACK: # BACK is on TOP because close and no other action needs
            self.close()
            return

        selectedItem: xbmcgui.ListItem
        pos = self.List.getSelectedPosition()
        selectedItem = self.List.getListItem(pos)
        selectedName = selectedItem.getLabel()
        selectedID = selectedItem.getUniqueID("ID")

        if control == MAKER:  #click on a CustomList or ADD Button
            listPrefix = ""
            if self.mode == FormMode.List:
                listPrefix = "Personal"
            elif self.mode == FormMode.UserList:
                listPrefix = "User"

            newListName = "{} List {}".format(listPrefix, len(settingsCustomLists) + 1)

            addNew = not selectedName
            if not addNew:
                newListName = selectedName

            custom = customlist.CustomList("", TypeOfList=ListType.Personal, Name=newListName)
            m3uList = M3UList(Name=newListName)
            m3uList.IsValid = True

            if addNew:
                if self.mode == FormMode.UserList:
                    custom.Id = m3uList.Id
                    custom.TypeOfList = ListType.User
                    custom.Lists.append(m3uList)
            else:
                custom = self.getCustomListByID(selectedID)

            needsSave = False
            if self.mode == FormMode.List:
                needsSave, m3uList = compiledialog(m3uList)
                custom.Name = m3uList.Name
            elif self.mode == FormMode.UserList:
                m3uList.IsUserList = True
                needsSave, custom.Lists[0] = compiledialog(custom.Lists[0])
                custom.Name = custom.Lists[0].Name

            if needsSave:
                selectedItem = self.getListItem(custom.Name, custom.Id)
                selectedID = selectedItem.getUniqueID("ID")

                if addNew:
                    self.list.insert(-1, selectedItem)
                    pos = len(self.list) - 1  #get the position just inserted before the "+" button
                else:
                    self.list[pos] = selectedItem
                    settingsCustomLists.pop(self.getCustomListIdx(custom))

                settingsCustomLists.append(custom)
                self.save()

                self.customList = custom

                if self.mode == FormMode.List:
                    self.chooseAvailableLists(pos)
                elif self.mode == FormMode.UserList:
                    #load groups in remoteLists because them are not available as the list from tvch
                    m3uList = custom.Lists[0]
                    self.updateRemoteLists(m3uList)
                    if listmanager.checkUserListFile(m3uList):
                        self.chooseAvailableGroups(pos, selectedID)
                    #fileCheck = listmanager.getUserListFile(m3uList) != ""
                    #if fileCheck:
                    #    m3uList4RemoteObject = addGroupsToM3UListUser(m3uList)
                    #    if m3uList in remoteLists:
                    #        remoteLists.remove(m3uList)
                    #    remoteLists.append(m3uList4RemoteObject)
                    #    self.chooseAvailableGroups(pos, selectedID)
                    else:
                        utils.MessageBox("File download/check failed")

            self.loadList(pos)

        elif control == LIST:
            itemSelected = "selected"
            if self.mode == FormMode.List:  #only if List
                m3uList = self.selectOrCreateM3UList(selectedID, selectedName)
                idx = self.customList.index(m3uList)
                if selectedItem.getProperty("selected") != itemSelected:
                    self.customList.Lists[idx].Groups = [ALL_GROUPS_SELECTED]
                else:
                    itemSelected = "unselected"
                    del self.customList.Lists[idx]

                selectedItem.setProperty("selected", itemSelected)

            self.loadList(pos)

        elif control == BTN_GROUPS_SELECT_ALL:
            #m3uList = self.selectOrCreateM3UList(selectedID, selectedName)
            #idx = self.customList.index(m3uList)
            #self.customList.Lists[idx].Groups == [ALL_GROUPS_SELECTED]
            pass

        elif control == BTN_GROUPS_UNSELECT_ALL:
            #m3uList = self.selectOrCreateM3UList(selectedID, selectedName)
            #idx = self.customList.index(m3uList)
            #self.customList.Lists[idx].Groups == []
            pass

        elif control == BTN_GROUPS_CHOSEN: #button to choose groups (official lists personalization)
            itemSelected = ""
            m3uList = self.selectOrCreateM3UList(selectedID, selectedName)
            idx = self.customList.index(m3uList)
            self.chooseAvailableGroups(pos, selectedID)

            if self.customList.Lists[idx].AllGroupsSelected():
                itemSelected = "selected"
            elif len(self.customList.Lists[idx].Groups) > 0:
                itemSelected = "partial"
            else:
                itemSelected = "unselected"

            selectedItem.setProperty("selected", itemSelected)
            self.loadList(pos)

        elif control == GROUPS:
            itemSelected = "selected"
            if selectedItem.getProperty("selected") != itemSelected:
                self.Groups.append(selectedID)
            else:
                self.Groups.remove(selectedID)
                itemSelected = "unselected"

            selectedItem.setProperty("selected", itemSelected)


        elif control == BTN_LIST_MOVE_UP:
            self.moveListItem(pos, -1, control)

        elif control == BTN_LIST_MOVE_DOWN:
            self.moveListItem(pos, 1, control)

        elif control == BTN_LIST_GROUPS_CHOOSE:  #button to choose lists (or groups if userlist)
            self.customList = self.getCustomListByID(selectedID)

            if self.mode == FormMode.List:
                self.chooseAvailableLists(pos)
            elif self.mode == FormMode.UserList:
                self.chooseAvailableGroups(pos, selectedID)

            self.loadList(pos)

        elif control == BTN_LIST_GROUPS_RESET:
            if self.mode == FormMode.UserList:
                self.resetGroups(selectedID)

        elif control == BTN_LIST_DELETE:
            
            if utils.MessageBoxQuestion(config.getString(30186).format(selectedName)): #"Are you sure you want to delete the list {}"
                self.list.pop(pos)
                settingsCustomLists.pop(pos)
                self.save()
                self.loadList(pos)
                listmanager.deleteList(selectedID)

        elif control == BTN_LIST_REFRESH:
            if self.mode == FormMode.UserList:
                self.refreshList(selectedID)

    def moveListItem(self, pos: int, value2Add: int, control):
        newpos = pos + value2Add
        if (newpos > -1 and value2Add < 0) or (newpos < len(self.list) - 1 and value2Add > 0):
            self.list[pos], self.list[newpos] = self.list[newpos], self.list[pos]
            settingsCustomLists[pos], settingsCustomLists[newpos] = settingsCustomLists[newpos], settingsCustomLists[pos]

            self.save()
            self.loadList(newpos, control)

    def selectOrCreateM3UList(self, selectedID, selectedName):
        m3uList = self.getCustomChoosenListByID(selectedID, SearchCustomFrom.Current)

        if not m3uList:
            m3uList = M3UList(selectedID, selectedName)
            m3uList.IsValid = True
            self.customList.Lists.append(m3uList)

        return m3uList

    def getCustomChoosenListByID(self, selectedID: str, searchFrom: SearchCustomFrom) -> M3UList:
        res = None
        if (searchFrom == SearchCustomFrom.Settings):
            for cl in settingsCustomLists:
                res = next((x for x in cl.Lists if x.Id == selectedID), None)
                if res: break
        elif (searchFrom == SearchCustomFrom.Current):
            res = next((x for x in self.customList.Lists if x.Id == selectedID), None)

        return res

    def getCustomChoosenListIndexByID(self, selectedID: str, searchFrom: SearchCustomFrom) -> int:
        res = self.getCustomChoosenListByID(selectedID, searchFrom)
        return self.customList.Lists.index(res)

    def getCustomListByID(self, selectedID: str) -> CustomList:
        return next((x for x in settingsCustomLists if x.Id == selectedID), None)

    def getCustomListIdx(self, custom: CustomList) -> int:
        return settingsCustomLists.index(custom)

    def onAction(self, action):
        action = action.getId()
        if action in [EXIT, BACKSPACE]:
            self.close()

    def showLists(self, availableLists: List[M3UList]):
        logger.debug("Enter in: ", inspect.currentframe().f_code.co_name)
        for availableM3uList in availableLists:
            itemSelected = "unselected"
            item = self.getListItem(availableM3uList.DisplayName, availableM3uList.Id)

            if len(availableM3uList.Groups) > 1:
                item.setProperty("groups", "true")
            m3uList = self.getCustomChoosenListByID(availableM3uList.Id, SearchCustomFrom.Current)

            if m3uList:
                if m3uList.AllGroupsSelected():
                    itemSelected = "selected"
                elif m3uList.Groups:
                    itemSelected = "partial"

            item.setProperty("selected", itemSelected)
            self.list.append(item)

    def showGroups(self, listGroupsId: str):
        logger.debug("Enter in: ", inspect.currentframe().f_code.co_name)

        availableGroups = self.getAvailableGroups(listGroupsId)
        m3uList = self.getCustomChoosenListByID(listGroupsId, SearchCustomFrom.Current)

        getAllAvailable = (self.mode == FormMode.List and m3uList.AllGroupsSelected()) \
                       or (self.mode == FormMode.UserList and (not m3uList.Groups or m3uList.AllGroupsSelected()))

        if getAllAvailable: #self.mode == FormMode.UserList and not m3uList.Groups:
            self.Groups = list(map(lambda item: item.Id, availableGroups))
        else:
            self.Groups = m3uList.Groups.copy()
        
        for group in availableGroups:
            itemSelected = "unselected"
            item = self.getListItem(group.Description, group.Id)

            if getAllAvailable: #(self.mode == FormMode.List and m3uList.AllGroupsSelected()) or (self.mode == FormMode.UserList and not m3uList.Groups):
                itemSelected = "selected"
            elif group.Id in m3uList.Groups:
                itemSelected = "selected"

            item.setProperty("selected", itemSelected)
            self.list.append(item)

    def chooseAvailableLists(self, pos: int):
        logger.debug("Enter in: ", inspect.currentframe().f_code.co_name)
        custom = launch(LIST, self.mode, self.customList)

        settingsCustomLists.pop(self.getCustomListIdx(custom))
        if custom.Lists:
            settingsCustomLists.append(custom)
        else:
            self.list.pop(pos)

        self.save()

    def chooseAvailableGroups(self, pos: int, listGroupsId: str):
        logger.debug("Enter in: ", inspect.currentframe().f_code.co_name)
        custom = self.customList
        groups = launch(GROUPS, self.mode, custom, listGroupsId)
        m3uList = self.getCustomChoosenListByID(listGroupsId, SearchCustomFrom.Current)
        availableGroups = self.getAvailableGroups(listGroupsId)

        if availableGroups:
            allGroups = list(map(lambda item: item.Id, availableGroups))

            idx = self.customList.index(m3uList)
            self.customList.Lists[idx].Groups = groups.copy()

            if len(self.customList.Lists[idx].Groups) == len(allGroups):
                self.customList.Lists[idx].Groups = [ALL_GROUPS_SELECTED] if FormMode.List else []

            settingsCustomLists.pop(self.getCustomListIdx(custom))
            if custom.Lists:
                settingsCustomLists.append(custom)
            else:
                self.list.pop(pos)

            self.save(self.customList.Lists[idx])

    def refreshList(self, listGroupsId: str):
        logger.debug("Enter in: ", inspect.currentframe().f_code.co_name)
        m3uList = self.getCustomChoosenListByID(listGroupsId, SearchCustomFrom.Settings)
        
        if(m3uList):
            listmanager.deleteList(listGroupsId)
            self.resetGroups(listGroupsId, True)

    def resetGroups(self, listGroupsId: str, bypassQuestion: bool = False):
        logger.debug("Enter in: ", inspect.currentframe().f_code.co_name)
        m3uList = self.getCustomChoosenListByID(listGroupsId, SearchCustomFrom.Settings)

        if bypassQuestion or utils.MessageBoxQuestion(config.getString(30187).format(m3uList.DisplayName)): #"Are you sure you want to set all groups for the list {}"
            m3uList.Groups = []
            self.updateRemoteLists(m3uList)
            #self.save(m3uList)

    def updateRemoteLists(self, m3uList: M3UList):
        m3uList4RemoteObject = addGroupsToM3UListUser(m3uList)
        if m3uList4RemoteObject:
            rList = next( iter( filter( lambda c: (c.Id == m3uList.Id), remoteLists ) ) )
            remoteLists.pop(remoteLists.index(rList))
            if m3uList in remoteLists:
                remoteLists.remove(m3uList)
            remoteLists.append(m3uList4RemoteObject)
            return True
        return False

    def loadList(self, idx, button=None):
        self.List.reset()
        self.List.addItems(self.list)
        self.setFocusId(self.windowType)
        self.List.selectItem(idx)
        if button:
            self.setFocusId(button)

    def getListItem(self, name, id):
        item = xbmcgui.ListItem(name)
        item.setUniqueIDs({"ID": id})
        return item

    def getAvailableGroups(self, listGroupId) -> List[M3UGroupItem]:
        groups = next((x.Groups for x in remoteLists if x.Id == listGroupId), None)
        return list(map(lambda item: M3UGroupItem.from_dict(item), groups))

    def save(self, m3uList: M3UList = None):
        strSetting = json.dumps(settingsCustomLists, default=lambda x: x.to_dict())

        if self.mode == FormMode.List:
            listmanager.setSettingsCustomLists(utils.PARAM_LIST_NAME, strSetting)
        elif self.mode == FormMode.UserList:
            listmanager.setSettingsCustomLists(utils.PARAM_USER_LIST_NAME, strSetting)
            if m3uList:
                listmanager.cleanup(listmanager.FileType.Groups, m3uList.Id) # clean the groups file, selections could be changed
                listmanager.cleanup(listmanager.FileType.Live,   m3uList.Id) # Also Live   file cleanup
                listmanager.cleanup(listmanager.FileType.Movies, m3uList.Id) # Also Movies file cleanup
                listmanager.cleanup(listmanager.FileType.Series, m3uList.Id) # Also Series file cleanup
                if utils.checkFileExists(listmanager.getUserListFile(m3uList)):
                    listmanager.getUserListFileLive(m3uList) #because of selections have been changed, i rebuild a new Live file with new filters applied
                    addGroupsToM3UListUser(m3uList)


class CompileDialog(xbmcgui.WindowXMLDialog):
    def start(self, m3ulist: M3UList = None):
        self.m3uList = m3ulist
        self.isValid = False

        self.doModal()

        self.m3uList.Name = self.getControl(TXT_DIALOG_NAME).getText()
        self.m3uList.DisplayName = self.m3uList.Name
        self.m3uList.List = self.getControl(TXT_DIALOG_LIST).getText()
        self.m3uList.Epg  = self.getControl(TXT_DIALOG_EPG).getText()

        return (self.isValid, self.m3uList)

    def onInit(self):
        self.getControl(TXT_DIALOG_LIST).setVisible(self.m3uList.IsUserList)
        self.getControl(TXT_DIALOG_EPG).setVisible(self.m3uList.IsUserList)
        self.getControl(BTN_DIALOG_LIST_SEARCH).setVisible(self.m3uList.IsUserList)
        self.getControl(BTN_DIALOG_EPG_SEARCH).setVisible(self.m3uList.IsUserList)

        self.getControl(TXT_DIALOG_NAME).setText(self.m3uList.Name)
        self.getControl(TXT_DIALOG_LIST).setText(self.m3uList.List)
        self.getControl(TXT_DIALOG_EPG).setText(self.m3uList.Epg)
        self.setFocusId(TXT_DIALOG_NAME)

    def onClick(self, control):
        if control == BTN_DIALOG_LIST_SEARCH:
            filePath = xbmcgui.Dialog().browseSingle(1, config.getString(30002), "files", ".m3u|.m3u8")
            self.getControl(TXT_DIALOG_LIST).setText(filePath)
        if control == BTN_DIALOG_EPG_SEARCH:
            self.getControl(TXT_DIALOG_EPG).setText(xbmcgui.Dialog().browse(1, config.getString(30135), "", ".gz|.gzip|.xz", True, False))
        if control == BTN_DIALOG_OK:
            self.isValid = True
            self.close()
        elif control == BTN_DIALOG_CANCEL:
            self.close()


class ListModeSelection(xbmcgui.WindowXMLDialog):
    def start(self):
        self.mode = None
        self.modes = {config.getString(30140):FormMode.List, config.getString(30139):FormMode.UserList, "Import Url":FormMode.ImportFromUrl, "Import File":FormMode.ImportFromFile }
        self.doModal()
        return self.mode

    def onInit(self):
        self.List = self.getControl(1)
        for name in self.modes.keys():
            self.List.addItem(xbmcgui.ListItem(name))
        self.setFocusId(1)
        self.List.selectItem(0)

    def onClick(self, control):
        if control == 1:
            self.mode = list(self.modes.values())[self.List.getSelectedPosition()]
        self.close()


def compiledialog(m3uList: M3UList = None):
    return CompileDialog("CompileDialog.xml", config.ADDON_PATH, "Default").start(m3uList)


def addGroupsToM3UListUser(m3uList: M3UList = None) -> M3UList :
    if m3uList:
        groups = list()

        if utils.checkFileExists(listmanager.getUserListFile(m3uList)):
            progress = xbmcgui.DialogProgress()
            progress.create(f"{m3uList.DisplayName} file scan", "Please wait. Scanning...")

            groups.extend(getM3UGroups(m3uList, M3UStreamType.LIVE))
            progress.update(round(100 * 1 / 3), f"Scanning: {M3UStreamType.LIVE} section")

            groups.extend(getM3UGroups(m3uList, M3UStreamType.MOVIES))
            progress.update(round(100 * 2 / 3), f"Scanning: {M3UStreamType.MOVIES} section")

            groups.extend(getM3UGroups(m3uList, M3UStreamType.SERIES))
            progress.update(round(100 * 3 / 3), f"Scanning: {M3UStreamType.SERIES} section")

            progress.close()

        tmp = copy.deepcopy(m3uList)
        tmp.Groups = groups.copy()
        return tmp


def getM3UGroups(m3uList: M3UList, streamType: M3UStreamType) -> List[M3UGroupItem]:
    groups = listmanager.getUserListGroup(m3uList, streamType)
    for idx, g in enumerate(groups): groups[idx] = M3UGroupItem(g, g, f"[{streamType}] {g}").to_dict()
    return groups


def launch(windowType = MAKER, mode: FormMode = None, custom: CustomList = None, listGroupId: str = ""):
    global remoteLists, settingsCustomLists

    if windowType == MAKER: # load all only during first run
        if not mode:
            ##ImportList().FromFile()
            mode = ListModeSelection("ListModeSelection.xml", config.ADDON_PATH, "Default").start()

        if not mode:
            return
        elif mode == FormMode.List:
            settingsCustomLists = listmanager.getSettingsCustomLists(utils.PARAM_LIST_NAME)
            if isServerOnLine:
                remoteLists = utils.getRemoteGroups()
            else:
                xbmcgui.Dialog().ok(utils.ADDON_NAME, "Server Off-Line, impossibile procedere in questo momento")
                return
        elif mode == FormMode.UserList:
            settingsCustomLists = listmanager.getSettingsCustomLists(utils.PARAM_USER_LIST_NAME)
            lists = list()
            for cl in settingsCustomLists:
                for m3uList in cl.Lists:
                    lists.append(addGroupsToM3UListUser(m3uList))

            remoteLists = lists
        elif mode == FormMode.ImportFromUrl:
            ImportList().From(PathImportType.Url)
            return;
        elif mode == FormMode.ImportFromFile:
            ImportList().From(PathImportType.File)
            return;
            

    return ListMaker("ListMaker.xml", config.ADDON_PATH, "Default").start(windowType=windowType, mode=mode, custom=custom, listGroupId=listGroupId)


class ImportList():
    def From(self, pathImportType: PathImportType):
        if pathImportType == PathImportType.Url:
            path = utils.MessageBoxInput("Insert Url or Path").strip()
        elif pathImportType == PathImportType.File:
            path = xbmcgui.Dialog().browseSingle(1, config.getString(30002), "files", ".txt")
        
        fileContentLines = ""
        
        if pathImportType == PathImportType.Url:
            try:
                fileContentLines = requests.get(path).text.splitlines()
            except:
                utils.MessageBox("Invalid Url provided")
        elif pathImportType == PathImportType.File:
            if utils.checkFileExists(path):
                _tmpFile = utils.getPersonalPathFile("~~tmp.txt")
                xbmcvfs.copy(path, _tmpFile)
                fileContentLines = utils.readFileAllRows(_tmpFile)
                xbmcvfs.delete(_tmpFile)

        if fileContentLines:
            if self.Import(fileContentLines):
                utils.MessageBox("Import Done")

    def Import(self, fileContentLines):
        if fileContentLines:
            linesCount = len(fileContentLines)
            for idx in range(linesCount):
                line = fileContentLines[idx].strip()
                if line.strip() == "": continue
                if line.startswith("#"): continue
                lineSplit = line.split("#$$#")
                newListName = lineSplit[0]
                newListName = f"{newListName}"
                newListUrl =  lineSplit[1]
                newListEPG =  lineSplit[2]

                m3uList = M3UList(Name=newListName)
                m3uList.IsValid = True
                m3uList.IsUserList = True
                m3uList.List = newListUrl
                m3uList.Epg = newListEPG

                custom = customlist.CustomList("", TypeOfList=ListType.Personal, Name=newListName)
                custom.Id = m3uList.Id
                custom.Name = m3uList.Name
                custom.TypeOfList = ListType.User
                custom.Lists.append(m3uList)

                settingsCustomLists = listmanager.getSettingsCustomLists(utils.PARAM_USER_LIST_NAME)

                if any(x for x in settingsCustomLists if x.Name == custom.Name):
                    utils.MessageBox(f"A list named {custom.Name} already exists, it'll be skipped.")
                else:
                    settingsCustomLists.append(custom)
                    strSetting = json.dumps(settingsCustomLists, default=lambda x: x.to_dict())

                    listmanager.setSettingsCustomLists(utils.PARAM_USER_LIST_NAME, strSetting)

            return True

        return False
