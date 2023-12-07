import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs
import xbmcaddon
import sys
import json
import base64
import zlib
import requests
import time
import datetime
import hashlib
import urllib
import uuid
import importlib

from xbmcvfs import translatePath
from urllib import request
from urllib.parse import urlencode
from typing import List
from lib import config, logger, install, const
from lib.customlist import CustomList, ListType
from lib.m3u.m3ulist import M3UList
from lib.m3u.m3uitem import M3UItem
from lib.playablemediaitem import PlayableMediaItem


ADDON_NAME = "World Live TV"

HOST = "https://www.worldtvlive.eu"
HOST_TVCH = "https://tvchannels.worldtvlive.eu"

API_DOMAIN = f"{HOST_TVCH}/tv"
FILE_REPO_URL = f"{HOST}/world/files"
ADDON_REPO_HOTFIX = "https://worldlivetv.github.io/repo/plugin.video.wltvhelper.hotfix"
EPG_URL = "http://epg-guide.com/wltv.xz"
VIDEO_NOT_FOUND = "https://worldlivetv.github.io/not_found.mp4"
LAST_CHK_INF = "lastcheck.inf"
SETTINGS_FILE = "settings.xml"
HOTFIX_FILE = "hotfix.zip"
HOTFIX_FILE_INFO = "hotfix.json"

EMR_DTT_FTA_FILE = "emr.bin"
TEMP_LISTFILE_NAME = "~temp.bin"

TEMP_FULL_USERLISTFILE_NAME = "~tempFullUser.bin"
TEMP_USERLISTFILE_NAME = "~tempUser.bin"

DEFAULT_DATE = 20210101

PARAM_LIST_NAME = "personal_list_v1"
PARAM_USER_LIST_NAME = "user_list_v1"
EXPIRING_LOCAL_FILES_DAYS = config.getSetting("localFileExpiringDays")
TAG_ADDON_KODILIST = "kodi"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
USER_AGENT_MOBILE = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Mobile Safari/537.36"

BETA_TOKEN = "566796c646c627f677"


def MessageBox(msg: str):
    if isinstance(msg, int):
        msg = config.getString(msg)
    xbmcgui.Dialog().ok(ADDON_NAME, msg)

def MessageBoxQuestion(msg: str):
    if isinstance(msg, int):
        msg = config.getString(msg)
    return xbmcgui.Dialog().yesno(ADDON_NAME, msg)

def MessageNotification(msg: str, seconds: int = 0):
    if isinstance(msg, int):
        msg = config.getString(msg)
    xbmcgui.Dialog().notification(ADDON_NAME, message = msg, time = seconds * 1000) 

def MessageBoxInput(msg: str, inputStr: str = ""):
    if isinstance(msg, int):
        msg = config.getString(msg)
        if not msg: msg = ADDON_NAME
    return xbmcgui.Dialog().input(msg, inputStr, type = xbmcgui.INPUT_ALPHANUM) 


def getBrowserHeaders() -> dict:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,de;q=0.6",
        "Upgrade-Insecure-Requests": "1"
    }
    return headers


def apiRequester(par=""):
    return requests.get(API_DOMAIN + par, timeout=5).json()


def getScriptFileName(fileName):
    return os.path.splitext(os.path.basename(fileName))[0]


def checkServerOnLine():
    res = False
    if config.getSetting("emulateServerOffLine") and config.isBeta() == True:
        logger.info("Emulation Server off-line is set to True")
        return res

    try:
        isOnLine = requests.get(HOST_TVCH + "/online",  timeout=2).status_code
        res = isOnLine == 204
    except:
        pass

    if not res:
        logger.info("Server off-line or server error")

    return res


def isGzFile(filepath):
    with open(filepath, 'rb') as tmpFile:
        return tmpFile.read(2) == b'\x1f\x8b'


def decompressGZFile(infile: str, tofile: str):
    import gzip
    with open(infile, 'rb') as inf:
        _str = gzip.decompress(inf.read()).decode('utf-8')

    with open(tofile, 'w', encoding='utf8') as tof:
        tof.write(_str)


def readFile(fullFileName):
    file = xbmcvfs.File(fullFileName)
    fileContent = file.read()
    file.close()

    return fileContent


def readFileAllRows(fullFileName):
    l = list()
    with open(fullFileName, 'r') as f:
        l = f.readlines()
        f.close()

    return l


def writeFile(filePath, input):
    file = xbmcvfs.File(filePath, "w")
    file.write(input)
    file.close()


def downloadFile(url, filePath, returnContent=False, headers: dict = None, timeout = None):  # duplice funzione
    req = requests.get(url, allow_redirects=True, headers=headers, timeout=timeout)
    if filePath != "":
        writeFile(filePath, req.content)
    if returnContent:
        return req.content


def extract(zipFilePath, destination):  # alternative to xbmc.executebuiltin(Extract
    import zipfile  # non serve altrove

    with zipfile.ZipFile(zipFilePath, "r") as zip:
        zip.extractall(destination)


def getPersonalPathFile(filename):
    filePath = os.path.join(config.ADDON_USER_PATH, filename)

    return translatePath(filePath)


def getPersonalSubPathFile(subDir, filename):
    filePath = os.path.join(config.ADDON_USER_PATH, subDir, filename)

    return translatePath(filePath)


def createSubDir(subDir):
    if subDir:
        path = translatePath(os.path.join(config.ADDON_USER_PATH, subDir))
        if not os.path.isdir(path):
            os.mkdir(path)


def getFiles(dir: str = config.ADDON_USER_PATH, searchPattern: str = "*") -> list():
    import glob

    files = list()
    dirPath = translatePath(dir)
    patterns = searchPattern.split(",")

    for ext in patterns : files.extend(glob.glob(dirPath + ext))

    return list(set(files))


def readLocalOrDownload(repoUrl, subDir, fileName, sameRemoteSub = False, checkServerFileTimeStamp = True, onceaday = True):
    fileContent = ""
    createSubDir(subDir)
    filePath = getPersonalSubPathFile(subDir, fileName)
    remotePath = repoUrl
    subDir = subDir.lower()

    if sameRemoteSub:
        remotePath = f"{repoUrl}/{subDir}"
    forceDownload = serverFileNeedsUpdate(subDir, fileName, remotePath, checkServerFileTimeStamp, onceaday)

    if not forceDownload:
        try:
            fileContent = readFile(filePath)
        except:
            fileContent = ""

    if not fileContent or forceDownload:
        url = f"{remotePath}/{fileName}"
        fileContent = downloadFile(url, filePath, True)

    return fileContent


def readLocalOrDownloadFromUrl(url, subDir, fileName, makePing, onceaday = True):
    fileContent = ""
    createSubDir(subDir)
    filePath = getPersonalSubPathFile(subDir, fileName)
    subDir = subDir.lower()

    forceDownload = not os.path.isfile(filePath)

    if not forceDownload:
        try:
            fileContent = readFile(filePath)
        except:
            fileContent = ""

        last_modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(filePath)).date()
        today = datetime.datetime.now().date()

        if onceaday:
            forceDownload = today >= last_modified_date

    if not fileContent or forceDownload:
        try:
            pingOk = False
            if makePing:
                pingOk = ping(url)

            if pingOk:
                fileContent_tmp = downloadFile(url, filePath, True)
                if fileContent_tmp:
                    fileContent = fileContent_tmp 
        except :
            logger.error(f"downloadFile error {fileName}")
            pass

    return fileContent


def ping (url, count = 1):
    from re import findall
    from subprocess import Popen, PIPE
    o = urllib.parse.urlparse(url)
    host = o.hostname
    
    data = ""
    output = Popen(f"ping {host} -n {count}", stdout = PIPE, encoding = "utf-8")

    for line in output.stdout:
        data = data + line
        
    res = findall("TTL", data)

    return len(res) > 0

def serverFileNeedsUpdate(subDir, fileName, remotePath, checkServerFileTimeStamp=False, onceaday=True):
    res = False
    if not checkServerOnLine():
        return res

    filePath = getPersonalSubPathFile(subDir, fileName)

    logger.debug(f"Check update for File: {subDir}/{fileName}, FromServer: {checkServerFileTimeStamp}, Once a Day: {onceaday}")
    if not checkFileExists(filePath):
        logger.info(f"Cannot get localfile {subDir}/{fileName}, needs update")
        res = True
    else:
        try:
            if checkServerFileTimeStamp:
                last_modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(filePath))
                day = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][last_modified_date.weekday()]

                if onceaday:
                    modified_since = last_modified_date.strftime("%d %b %Y 23:59:59 GTM")  # once a day it's enought
                else:
                    modified_since = last_modified_date.strftime("%d %b %Y %H:%M:%S GTM")

                url = f"{remotePath}/{fileName}"
                req = requests.get(url,headers={"If-Modified-Since": f"{day}, {modified_since}"}, timeout=5)
                status = req.status_code

                #if status == 404:  # not found on server
                #    res = False
                #elif (req.status_code != 304):  # cannot read from local file because of CACHE, needs update
                #    res = True

                if status == 200:  # OK .. it's modified, needs update
                    res = True
                logger.debug(f"Query status code: {req.status_code} is changed: {res}")
            else:
                dt = datetime.datetime.now()
                file_datetime = datetime.datetime.fromtimestamp(os.path.getctime(filePath))
                res = (dt - file_datetime).days > 1
        except OSError as e:
            if "HTTPConnectionPool" in str(e):
                logger.error(f"Error getting remote file info {fileName}, cannot check update", e)
                res = False
            else:
                logger.error(f"Error getting local file info {fileName}, needs update", e)
                res = True
        except Exception as e:
            logger.error(f"Error during serverFileNeedsUpdate check: [{e}]")
            logger.error(f"Force download {fileName}")
            res = True

    return res


def localFileNeedsUpdate(filePath):
    res = True

    if(checkFileExists(filePath)):
        fileDate = datetime.datetime.fromtimestamp(os.path.getmtime(filePath)) + datetime.timedelta(days=EXPIRING_LOCAL_FILES_DAYS)
        dtFile = int(fileDate.strftime("%Y%m%d"))
        dtNow  = int(datetime.date.today().strftime("%Y%m%d"))
        res = dtNow > dtFile

    return res


def checkForUpdates():
    logger.debug("starts...")
    res = False

    # if directory ADDONUSERPATH doesn't exist (first launch after installation)
    # I create it manually to get first Updates if needs
    isExistAddonDirectory = checkFileExists(translatePath(config.ADDON_USER_PATH))
    if not isExistAddonDirectory:
        os.makedirs(translatePath(config.ADDON_USER_PATH))

    if config.isDEV():
        logger.info("YOU ARE IN DEV MODE: checkupdates has been disabled")
        return

    itsTimeToCheck = False
    fileTimer = getPersonalPathFile(LAST_CHK_INF)

    if checkFileExists(fileTimer):
        t = time.time() - os.path.getmtime(fileTimer)
        if t > 3600:  # check ogni ora
            itsTimeToCheck = True
    else:
        itsTimeToCheck = True

    logger.debug("itsTimeToCheck: ", itsTimeToCheck)
    if itsTimeToCheck:
        try:
            res = installUpdates()
        except:
            pass

        writeFile(fileTimer, str(datetime.datetime.fromtimestamp(time.time())))

    return res


def getCurrentVersionAndHotfix():
    hotfixLocalNumber = 0
    vers=config.ADDON_VERSION.split("~")

    versInt=vers[0]
    versStr=""

    if len(vers) == 1:
        addonVersionNumber = int(versInt.replace(".", ""))
        localHotfixInfoFile = getPersonalPathFile(HOTFIX_FILE_INFO)

        if os.path.isfile(localHotfixInfoFile):
            hotfixLocalJson = json.loads(readFile(localHotfixInfoFile))
            verLocalNumber = int(hotfixLocalJson["version"].replace(".", ""))

            if verLocalNumber >= addonVersionNumber:
                hotfixLocalNumber = hotfixLocalJson["hotfix"]
    else:
        versStr=vers[1]

    return config.ADDON_VERSION, hotfixLocalNumber


def getCurrentVersionAndHotfixString():
    vers, hotfix = getCurrentVersionAndHotfix()

    version_string = str(vers)
    if hotfix != "0" and hotfix != 0:
        version_string = f"{version_string} (hotfix:{hotfix})"

    strMsg = config.ADDON.getLocalizedString(30134)
    strMsg = strMsg.format(version_string)
    return strMsg


def getApikeyParameter():
    admin_token = getAdminToken()
    if not admin_token:
        admin_token = ""
    else:
        admin_token = "apikey={}&".format(admin_token)

    return admin_token


def getAdminToken():
    FILE = translatePath(os.path.join(config.ADDON_PATH, "admin_token"))
    if os.path.isfile(FILE):
        token = readFile(FILE)
        logger.info(f"we found an \"admin_token\" file. Try to use: {token}")
        return token

    if config.isBeta():
        return BETA_TOKEN
    else:
        return None


def getRandomID(lenght:int)->str:
    uId = str(uuid.uuid4()).replace("-", "")
    if(lenght>len(uId)):
        return uId
    else:
        return uId[:lenght]


def installUpdates():
    res = False
    verServerString = ""
    verServerNumber = 0
    hotfixServerNumber = 0
    hotfixFileServer = ""
    verLocalNumber = 0
    hotfixLocalNumber = 0
    updateDescription = ""

    url = "{}/{}".format(ADDON_REPO_HOTFIX, HOTFIX_FILE_INFO)
    localHotfixInfoFile = getPersonalPathFile(HOTFIX_FILE_INFO)

    try:
        hotfixServerJson = requests.get(url).json()

        for hotfixServer in hotfixServerJson:
            verServerString = hotfixServer["version"]
            verDestination = hotfixServer["destination"]
            if verDestination == config.ADDON_VERSION:
                verServerNumber = int(verServerString.replace(".", ""))
                hotfixFileServer = hotfixServer["filename"]
                typeofupdate = hotfixServer["type"]
                hotfixServerNumber = hotfixServer["hotfix"]
                updateDescription = hotfixServer["description"]
                break

        if os.path.isfile(localHotfixInfoFile):
            hotfixLocalJson = json.loads(readFile(localHotfixInfoFile))
            verLocalNumber = int(hotfixLocalJson["version"].replace(".", ""))
            hotfixLocalNumber = hotfixLocalJson["hotfix"]
    except:
        pass  # local json do not exists, I keep default values

    updateAvailable = (verServerNumber > verLocalNumber) or (verServerNumber == verLocalNumber and hotfixServerNumber > hotfixLocalNumber)

    if updateAvailable:
        dataFile = getPersonalPathFile(HOTFIX_FILE)
        logger.info(f"A new {typeofupdate} update (v.{verServerString}.{hotfixServerNumber}) is available... download and install...")
        if os.path.isfile(dataFile):
            os.remove(dataFile)

        url = f"{ADDON_REPO_HOTFIX}/{hotfixFileServer}"
        downloadFile(url, dataFile)

        # extract(dataFile, config.ROOTADDONPATH)
        xbmc.executebuiltin(f"Extract({dataFile}, {config.ADDON_ROOT_PATH})")
        xbmc.executebuiltin("UpdateLocalAddons")
        # xbmc.executebuiltin("UpdateAddonRepos")
        xbmc.sleep(1500)

        writeFile(localHotfixInfoFile, str(json.dumps(hotfixServer)))
        writeFile(dataFile, "update applied")
        logger.info(f"New {typeofupdate} update (v.{verServerString}.{hotfixServerNumber}) installed")
        strmsg = config.ADDON.getLocalizedString(30133)
        strmsg = strmsg.format(typeofupdate, verServerString, hotfixServerNumber)
        strmsg = f"{strmsg}\n\n{updateDescription}"
        xbmcgui.Dialog().ok(ADDON_NAME, strmsg)
        # xbmc.executebuiltin('Notification({}, {}, {})'.format(ADDON_NAME, strmsg, 4000))
        res = True
    else:
        logger.debug("No updates available, exit.")

    return res


def forceCheckUpdate(forceHotfix=False):
    logger.debug("Force check update")
    dir = translatePath(config.ADDON_USER_PATH)
    file = os.path.join(dir, LAST_CHK_INF)
    if os.path.isfile(file):
        os.remove(file)

    if forceHotfix:
        logger.debug("Force hotfix is true")
        file = os.path.join(dir, HOTFIX_FILE_INFO)
        if os.path.isfile(file):
            os.remove(file)

    res = checkForUpdates()
    if not res:
        xbmc.executebuiltin("Notification({}, {}, {})".format(ADDON_NAME, "No hotfix available", 4000))


def cacheCleanup():
    logger.debug("Start cache file cleanup")

    cleanupFiles("*.bin,*.dat,*.lst,~*")

    logger.debug("Cache file cleanup completed")
    xbmc.executebuiltin("Notification({}, {}, {})".format(ADDON_NAME, "Cache files has been cleanup!", 4000))


def cleanupFiles(searchPattern: str):
    if not searchPattern:
        return

    logger.debug(f"Start file cleanup: {searchPattern}")
    userFiles = getFiles(searchPattern=searchPattern)

    for filename in userFiles:
        if os.path.isfile(filename):
            logger.debug("Delete: ", filename)
            os.remove(filename)

    logger.debug("File cleanup completed")


def decompressFile(fileName, subDir = "", sameRemoteSubDir = False):
    fileContent = readLocalOrDownload(FILE_REPO_URL, subDir, fileName, sameRemoteSubDir)
    decomp = ""
    try:
        decomp = zlib.decompress(base64.b64decode(fileContent), -15)
    except Exception as e:
        logger.error("Error decompressing files: ", e)

    return decomp

def decompressString(input, encoding="ascii"): # "ascii", "utf8"
    """
        ** decompress **

        Decompress a Base64 string

        :param encoding: encoding string like "ascii" or "utf8"

        Example::
            ..
            string = decompressString(compressed_base64_string, "ascii")
            ..
    """
    string = ""
    if input:
        try:
            string = zlib.decompress(base64.b64decode(input.encode(encoding))).decode(encoding)
        except Exception as e:
            logger.error("Error decompressing: ", e)

    return string

def compressString(input, encoding="ascii"):   # "ascii", "utf8"
    """
        ** compress **

        Compress a string into Base64 string

        :param encoding: encoding string like "ascii" or "utf8"

        Example::
            ..
            string = compressString(plain_text_string, "ascii")
            ..
    """
    string = ""
    if input:
        try:
            string = base64.b64encode(zlib.compress(input.encode(encoding), 9)).decode(encoding)
        except Exception as e:
            logger.error("Error compressing: ", e)

    return string


def toBase64(input, encoding="utf8"):
    return base64.b64encode(input.encode(encoding)).decode(encoding)

def fromBase64(input, encoding="utf8"):
    return base64.b64decode(input.encode(encoding)).decode(encoding)


def getFileFullPath(fileName, subDir = ""):
    return translatePath(os.path.join(config.ADDON_USER_PATH, subDir, fileName))


def getRemoteLists() -> List[CustomList]:
    res = list()
    jsonLists = list()
    jsonListsEL  = getEmergencyDTTFtaList()

    fileFullName = getFileFullPath("lists.bin")

    if checkServerOnLine():
        try:
            jsonLists = apiRequester("/all.json")
            if localFileNeedsUpdate(fileFullName):
                writeFile(fileFullName, json.dumps(jsonLists))
        except Exception as ex:
            logger.error("Error during get online available lists")
            logger.error(ex)
    else: #try locally
        try:
            for item in jsonListsEL: jsonLists.append(item)
            jsonListsLCL = json.loads(readFile(fileFullName))
            for item in jsonListsLCL:
                if not item.get("DisplayName",""): item["DisplayName"] = item["Name"]
                item["DisplayName"] = item["DisplayName"] + " (cached)"
                jsonLists.append(item)
        except Exception as ex:
            logger.error("Error during get local available lists")
            logger.error(ex)

    for item in jsonLists:
        m3u = M3UList.from_dict(item)
        m3u.Id = m3u.Name
        custom = CustomList(m3u.Id, m3u.DisplayName, ListType.Official, [m3u])
        isOfficial2Add = (m3u.Enabled or config.isDEV() or config.isBeta()) and TAG_ADDON_KODILIST in m3u.Tags
        
        if m3u.IsEmergency:
            custom.TypeOfList = ListType.Emergency

        if m3u.IsEmergency or isOfficial2Add:
            res.append(custom)

        if isOfficial2Add:
            cacheFilesIfNeeds(custom)

    return res


def cacheFilesIfNeeds(customLists):
    getOnlineOrLocalCacheLink(computeListUrl(customLists))


def getRemoteGroups() -> List[M3UList]:
    res = list()
    jsonLists = list()
    fileFullName = getFileFullPath("groups.bin")

    if checkServerOnLine():
        try:
            jsonLists = apiRequester("/all/groups.json")

            if(localFileNeedsUpdate(fileFullName)):
                writeFile(fileFullName, json.dumps(jsonLists))
        except Exception as ex:
            logger.error("Error during get online available groups")
            logger.error(ex)
    else:
        try:
            jsonLists = json.loads(readFile(fileFullName))
        except Exception as ex:
            logger.error("Error during get local available groups")
            logger.error(ex)

    for item in jsonLists:
        m3u = M3UList.from_dict(item)
        m3u.Id = m3u.Name

        isOfficial2Add = (m3u.Enabled or config.isDEV() or config.isBeta()) and TAG_ADDON_KODILIST in m3u.Tags

        if isOfficial2Add:
            res.append(m3u)
    return res


def getEmergencyDTTFtaList():
    dttFtaPath = translatePath(os.path.join(config.ADDON_PATH, "resources", EMR_DTT_FTA_FILE))
    return [{"Name": "Emergency", "DisplayName": "DTT FTA (Emergenza)", "List": dttFtaPath, "Epg": EPG_URL, "IsEmergency": True, "IsUserList": False, "IsValid": True}]


def getUserAgentForLink(url):
    return f"{url}|User-Agent={USER_AGENT}"


def checkSettings():
    useDL = config.getSetting("forceDirectLink")

    dt = int(datetime.datetime.now().date().strftime("%Y%m%d"))
    expDt = int(config.getSetting("forceDirectLinkExp"))

    if useDL == True and expDt == DEFAULT_DATE:
        config.setSetting("forceDirectLinkExp", dt)
        expDt = dt

    if abs(dt - expDt) >= 1:
        config.setSetting("forceDirectLink", False)
        config.setSetting("forceDirectLinkExp", DEFAULT_DATE)

    if config.isBeta():
        config.setSetting("isBeta", True)

    selected = config.getSetting(const.SELECTED_LIST)
    lastSelected = config.getSetting(const.LAST_SELECTED_ONLINE_LIST)

    if lastSelected and selected != lastSelected and checkServerOnLine():
        if MessageBoxQuestion(30182):
            jsonList = getRemoteLists()
            m3uList = next( iter( filter( lambda c: (c.Id == lastSelected), jsonList ) ) )
            setList(m3uList.Lists[0])

    return


def checkSetup():
    check = install.isOfficiallyInstalled()
    if not check:
        MessageBox(30190)
        return False

    #check = install.isUpdateEnabled()
    #if not check:
    #    MessageBox(30191)
    #    return True

    return True


def computeListUrl(selectedList: CustomList) -> str:
    link = "";
    apiKeyParameter = getApikeyParameter()

    if len(selectedList.Lists) == 1 and selectedList.TypeOfList == ListType.Official:
        # user has selected a full list
        selected = selectedList.Lists[0]
        link = f"{API_DOMAIN}/{selected.Id}/list.m3u8?{apiKeyParameter}"
    else:
        # user has selected a personal list
        selectedGroups = []
        for selected in selectedList.Lists:
            selectedGroups.append("{}={}".format(selected.Id, ",".join(selected.Groups)))
        link = "{}/all/groups/merge.m3u8?{}{}".format(API_DOMAIN, apiKeyParameter, "&".join(selectedGroups))
        
    return link


def getOnlineOrLocalCacheLink(url):
    fileFullName = getFileFullPath("{}.lst".format(hashlib.md5(url.encode('utf8')).hexdigest()))

    if checkServerOnLine():
        try:
            if localFileNeedsUpdate(fileFullName):
                request.urlretrieve(url, fileFullName)
        except Exception as ex:
            logger.error("Error during get online m3u")
            logger.error(ex)
    else: #try locally
        url = fileFullName

    return url

def refreshFileDate(input):
    if checkFileExists(input):
        _tmpFile = getPersonalPathFile("~tmp")
        xbmcvfs.copy(input, _tmpFile)
        xbmcvfs.delete(input)
        xbmcvfs.copy(_tmpFile, input)
        xbmcvfs.delete(_tmpFile)

    return True

def checkFileExists(input):
    return xbmcvfs.exists(input)


def checkUrlExists(input):
    res = False;
    if input.startswith("http"):
        try:
            headers = {"user-agent": USER_AGENT}
            res = requests.head(input, headers = headers).status_code == 200
        except Exception as ex:
            logger.error(ex)

    return res

def getInstalledVersion():
    kodiVersionInstalled = 0

    # retrieve kodi installed version
    jsonProperties = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }')
    #jsonProperties = unicode(jsonProperties, 'utf-8', errors='ignore')

    jsonProperties = json.loads(jsonProperties)
    #if jsonProperties.has_key('result') and jsonProperties['result'].has_key('version'):
    kodiVersionInstalled = int(jsonProperties['result']['version']['major'])
    
    return kodiVersionInstalled

####################################################

def setList(m3u: M3UList, isOffline: bool = False):
    isSimpleInstalled = install.installPvr()
    kodiVersion = getInstalledVersion()
    pvrVersion = install.getPvrSimpleVersion()
    isPvrInstances = pvrVersion >= "20.8.0"

    if isSimpleInstalled:
        simpleClient = xbmcaddon.Addon(install.ADDON_ID_PVR)
        
        if kodiVersion > 19:
            xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"'+install.ADDON_ID_PVR+'","enabled":false}}')

        pvrPath = simpleClient.getAddonInfo("profile")
        settingsFilePath = os.path.join(pvrPath, "settings.xml")
        settingsInstanceFilePath = os.path.join(pvrPath, "instance-settings-1.xml")
    
        settingsFilePath = translatePath(settingsFilePath)
        settingsInstanceFilePath = translatePath(settingsInstanceFilePath)
        userFiles = getFiles(pvrPath, "iptv.m3u.cache*,xmltv.xml.cache*") 

        for filename in userFiles:
            if os.path.isfile(filename): xbmcvfs.delete(filename)

        if simpleClient.getSetting("m3uPathType") != "1":
            simpleClient.setSetting("m3uPathType", "1")
        if simpleClient.getSetting("epgPathType") != "1":
            simpleClient.setSetting("epgPathType", "1")

        if m3u.Epg:
            if simpleClient.getSetting("logoFromEpg") != "2":
                simpleClient.setSetting("logoFromEpg", "2")
            if simpleClient.getSetting("epgUrl") != m3u.Epg:
                simpleClient.setSetting("epgUrl", m3u.Epg)
            elif simpleClient.getSetting("epgUrl") and not config.getSetting("enable_epg"):
                simpleClient.setSetting("epgUrl", "")
        else:
            simpleClient.setSetting("epgUrl", "")
            simpleClient.setSetting("logoFromEpg", "0")

        simpleClient.setSetting("m3uUrl", m3u.List)

        if kodiVersion > 19:
            simpleClient.setSetting("kodi_addon_instance_name", "WLTV")
            simpleClient.setSetting("kodi_addon_instance_enabled", "true")
            xbmcvfs.copy(settingsFilePath, settingsInstanceFilePath)
            if isPvrInstances:
                xbmcvfs.delete(settingsFilePath)
        
        m3uId = f"{m3u.Id}_offline" if isOffline else m3u.Id
        config.setSetting(const.SELECTED_LIST, m3uId) #Set selected list in settings

        # show a simple notification informing user new IPTV list has been set
        MessageNotification(config.getString(30120).format(m3u.DisplayName))

        if kodiVersion > 19:
            xbmc.sleep(3000)
            xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"'+install.ADDON_ID_PVR+'","enabled":true}}')


def setListInt(listName, m3uListUrl, epgUrl):
    m3u = M3UList()
    m3u.Name = listName
    m3u.List = m3uListUrl
    m3u.Epg = epgUrl
    setList(m3u)


def addMenuItem(handle, title, url, imagedir = "", icon = "", thumb = "", poster = "", fanart = "", isFolder = True):
    if imagedir == "":
        imagedir = "images"

    if isinstance(title, int):
        title = config.getString(title)

    li = xbmcgui.ListItem(title)
    li.setArt(
        {
            "icon"  : os.path.join(config.ADDON_PATH, "resources", imagedir, icon + ".png"),
            "thumb" : os.path.join(config.ADDON_PATH, "resources", imagedir, (thumb  if thumb  else icon) + ".png"),
            "poster": os.path.join(config.ADDON_PATH, "resources", imagedir, (poster if poster else thumb if thumb else icon) + ".png"),
            "fanart": os.path.join(config.ADDON_PATH, "resources", imagedir, (fanart if fanart else "wltv-background") + ".png"),
        }
    )

    xbmcplugin.addDirectoryItem(handle=handle, url=url, listitem=li, isFolder=isFolder)

def addMenuItemVideoM3U(handle, item: M3UItem):
    link = item.Link
    params = dict()
    if item.UserAgent:
        params["user-agent"]=item.UserAgent
    if item.Referer:
        params["referer"]=item.Referer
    if params:
        link = f"{item.Link}|{urlencode(params)}"
    return addMenuItemVideo(handle, item.Title, link, "", item.TvgLogo, isFolder=False)


def addMenuItemAudio(handle, title, url, plot="", icon="", thumb="", poster="", fanart="", genre=(), year="", isFolder=False):
    addMenuItemPlayable(handle, title, url, plot, icon, thumb, poster, fanart, genre, year, mediatype="audio", isFolder=isFolder)


def addMenuItemVideo(handle, title, url, plot="", icon="", thumb="", poster="", fanart="", genre=(), year="", isFolder=False):
    addMenuItemPlayable(handle, title, url, plot, icon, thumb, poster, fanart, genre, year, mediatype="video", isFolder=isFolder)


def addMenuItemPlayable(handle, title, url, plot="", icon="", thumb="", poster="", fanart="", genre=(), year="", mediatype="", isFolder=True):
    if isinstance(title, int):
        title = config.getString(title)

    li = xbmcgui.ListItem(title)

    #plot          string (Long Description)
    #plotoutline   string (Short Description)
    #title         string (Big Fan)
    #originaltitle string (Big Fan)
    #sorttitle     string (Big Fan)
    #title = title + "[CR]----"

    if not isFolder:
        li.setProperty("IsPlayable", "true")
        
    li.setInfo("video", {"title": title, "plot": plot, "plotoutline": plot, "genre": genre, "year": year, "mediatype": mediatype})

    li.setArt(
        {
            "icon":   icon,
            "thumb":  thumb  if thumb  else icon,
            "poster": poster if poster else icon,
            "fanart": fanart if fanart else icon,
        }
    )

    xbmcplugin.addDirectoryItem(handle=handle, url=url, listitem=li, isFolder=isFolder)


def getListItem(title, url, plot="", icon="", thumb="", poster="", fanart="", genre=(), year="", mediatype="", isFolder=True):
    if isinstance(title, int):
        title = config.getString(title)

    li = xbmcgui.ListItem(title)
    
    if not isFolder:
        li.setProperty("IsPlayable", "true")
        
    li.setInfo("video", {"title": title, "plot": plot, "plotoutline": plot, "genre": genre, "year": year, "mediatype": mediatype})

    li.setPath(url)
    li.setArt(
        {
            "icon":   icon,
            "thumb":  thumb  if thumb  else icon,
            "poster": poster if poster else icon,
            "fanart": fanart if fanart else icon,
        }
    )
    return li


def createPlayableMediaListItemsMenu(handle, name: str, showPosters: bool, listItems: List[PlayableMediaItem]):
    xbmcplugin.setPluginCategory(handle, name)

    seasons = set(list(map(lambda item: item.Season, listItems)))
    name = listItems[0].Title
    for s in seasons:
        if len(seasons) > 1:
            addMenuItem(handle, f"======== Season {str(s).zfill(2)} - {name} ========", "")

        episodes = list(filter(lambda item: item.Season == s, listItems))
        
        for item in episodes:
            thumb  = item.Thumbnail
            logo   = item.Fanart
            fanart = item.Fanart
            poster = item.Fanart
            isFolder = item.IsExternalLink #False

            if not showPosters:
                thumb  = ""
                logo   = "movie.png" if item.IsFilm else "tvshow.png"
                logo   = os.path.join(config.ADDON_PATH, "resources", logo)
                fanart = ""
                poster = ""

            addMenuItemVideo(handle, title=item.GetTitle(), url=item.Link, plot=item.Plot, icon=logo, thumb=thumb, poster=poster, fanart=fanart, genre=(), year="", isFolder=isFolder)

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(handle)


def getBroadcaster(broadcaster):
    c = importlib.util.find_spec(f"broadcaster.{broadcaster}")
    found = c is not None
    if found:
        c = importlib.import_module(f"broadcaster.{broadcaster}")
    else:
        MessageBox(f"Sorry, Plus broadcaster '{broadcaster}' not found")
        c = None

    return c


def vttToSrt(data):
    import re
    # Code adapted by VTT_TO_SRT.PY (c) Jansen A. Simanullang
    ret = ''

    data = re.sub(r'(\d\d:\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d:\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'\1,\2 --> \3,\4\n', data)
    data = re.sub(r'(\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'00:\1,\2 --> 00:\3,\4\n', data)
    data = re.sub(r'(\d\d).(\d\d\d) --> (\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'00:00:\1,\2 --> 00:00:\3,\4\n', data)
    data = re.sub(r'WEBVTT\n', '', data)
    data = re.sub(r'Kind:[ \-\w]+\n', '', data)
    data = re.sub(r'Language:[ \-\w]+\n', '', data)
    data = re.sub(r'<c[.\w\d]*>', '', data)
    data = re.sub(r'</c>', '', data)
    data = re.sub(r'<\d\d:\d\d:\d\d.\d\d\d>', '', data)
    data = re.sub(r'::[\-\w]+\([\-.\w\d]+\)[ ]*{[.,:;\(\) \-\w\d]+\n }\n', '', data)
    data = re.sub(r'Style:\n##\n', '', data)

    lines = data.split(os.linesep)

    for n, line in enumerate(lines):
        if re.match(r"((\d\d:){2}\d\d),(\d{3}) --> ((\d\d:){2}\d\d),(\d{3})", line):
            ret += str(n + 1) + os.linesep + line + os.linesep
        else:
            ret += line + os.linesep

    return ret
