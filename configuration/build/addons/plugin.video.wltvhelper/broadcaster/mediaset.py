# -*- coding: utf-8 -*-

from urllib3.exceptions import InsecureRequestWarning
import uuid, requests
from urllib.parse import urlencode
from lib import xmltodict, config, utils, scrapers, logger
from lib.broadcaster_result import BroadcasterResult

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

mpd = config.getSetting("mpd")

HOST = "https://mediasetinfinity.mediaset.it"

LOGIN_URL = "https://api-ott-prod-fe.mediaset.net/PROD/play/idm/anonymous/login/v2.0"
ALLSTATION_URL = "https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-stations-v2?sort=shortTitle|asc&form=cjson&httpError=true"
LICENSE_URL = "https://widevine.entitlement.theplatform.eu/wv/web/ModularDrm/getRawWidevineLicense?releasePid={pid}&account=http://access.auth.theplatform.com/data/Account/2702976343&schema=1.0&token={token}|Accept=*/*&Content-Type=|R{{SSM}}|"
STREAM_URL  = "https://api-ott-prod-fe.mediaset.net/PROD/play/playback/check/v2.0?sid={sid}"
ALL_JSON = "https://static3.mediasetplay.mediaset.it/apigw/nownext/nownext.json"

appName = ""
token = ""
sid   = ""

def play(search):
    global token, sid 
    clientId = str(uuid.uuid1())

    data = requests.get(HOST).text
    appName = scrapers.findSingleMatch(data, r'"app-name" content="([^"]+)')

    loginData = {
        "client_id": f"rtispa_mplayweb_{clientId}",
        "platform": "pc",
        "appName": appName
    }

    tkRes = requests.post(LOGIN_URL, json=loginData, verify=False)

    token = tkRes.json()["response"]["beToken"]
    sid   = tkRes.json()["response"]["sid"]

    return play_04(search)


def play_04(search):
    res = BroadcasterResult()

    url = ""
    pid = ""
    callSign = ""

    headers = utils.getBrowserHeaders()
    headers["Origin"]  = HOST
    headers["Referer"] = HOST

    # search
    if search.startswith("$"): 
        callSign = search[1:]
    else:
        items = requests.get(ALLSTATION_URL).json()["entries"]
        for item in items:
            if search.startswith("$"):
                _search = "$" + item["callSign"]
            else:
                _search = item["title"]

            if item.get("tuningInstruction", "") and _search == search:
                callSign = item["callSign"]
                break
        items = None

#RESTART URL
    #item = requests.get(ALL_JSON).json()["response"]["listings"][callSign]
    #item["stations"] = None
    #item["nextListing"] = None
    #item["currentListing"]["program"] = None
    #item["currentListing"]["description"] = ""
    #item["currentListing"]["mediasetlisting$epgTitle"] = ""

    #publicUrl = item["publicUrl"]
    #restartUrl = "" if "restartUrl" not in item["currentListing"] else item["currentListing"]["restartUrl"]
    #item = None

    jsonStreamRequestData = {
        "channelCode":f"{callSign}",
        "streamType":"LIVE",
        "delivery":"Streaming",
        "createDevice":"true",
        "overrideAppName": appName
    }

    headersStreamRequest = headers
    headersStreamRequest["Authorization"] = f"Bearer {token}"
    jsonStream = requests.post(STREAM_URL.format(sid=sid), json=jsonStreamRequestData, headers=headersStreamRequest).json()
    
    jsonUrlComposer = jsonStream["response"]["mediaSelector"]
    parameters = {x: jsonUrlComposer[x] for x in jsonUrlComposer if x not in ["url"]}
    parameters["auth"] = token

    #itemUrl = publicUrl if restartUrl == "" else restartUrl
    itemUrl = jsonStream["response"]["mediaSelector"]["url"]
    smilUrl = f"{itemUrl}?{urlencode(parameters)}"
    smilXml = requests.get(smilUrl).content.decode()

    xml = xmltodict.parse(smilXml)
    ref = xml["smil"]["body"]["seq"]["switch"]["ref"]
    par = ref["param"]
    url = ref["@src"] 
    
    isEncrypted = False if not "@security" in ref else ref["@security"] == "commonEncryption"
    pid = scrapers.findSingleMatch(par["@value"], r"\|pid=([^|]+)")

    if url:
        # set manifest for IA
        res.ManifestType = "hls"

        if mpd:
            res.ManifestType = "mpd"
            res.ManifestUpdateParameter = "full"
            if isEncrypted and pid:
                res.LicenseKey = LICENSE_URL.format(pid=pid, token=token)
        
        url = f"{url}|user-agent={utils.USER_AGENT}" #kodi 19 compatibility
        res.StreamHeaders = f"user-agent={utils.USER_AGENT}"
        res.Url = url
    else:
        logger.error("No url found for: ", search)
    
    return res


def play_03(search):
    res = BroadcasterResult()

    headers = utils.getBrowserHeaders()
    headers["Origin"]  = HOST
    headers["Referer"] = HOST
    
    url = ""
    pid = ""
    widevine = False
    forceMpd = mpd

    #strmFormat = "dash+xml" if mpd else "x-mpegURL"

    # get Json
    items = requests.get(ALLSTATION_URL, headers=headers).json()["entries"]

    mediasetRes = {"dash":{"url":"","pid":"","isWidevine":False },"mpeg":{"url":"","pid":"","isWidevine":False }}
    # search
    for item in items:
        title = item["title"]
        if search.startswith("$"):
            _search = "$" + item["callSign"]
        else:
            _search = item["title"]

        if item.get("tuningInstruction") and _search == search:

            for key in item["tuningInstruction"]["urn:theplatform:tv:location:any"]:
                isDash = False
                isMpeg = False

                strmFormat = "dash+xml"
                if key["format"] == "application/{}".format(strmFormat):
                    isDash = True
                else:
                    strmFormat = "x-mpegURL"
                    if key["format"] == "application/{}".format(strmFormat):
                        isMpeg = True

                if isDash or isMpeg:
                    try:
                        if "geoIT" in key["assetTypes"] or "geoNo" in key["assetTypes"] or "geoNoLim" in key["assetTypes"]:
                            k = "dash" if isDash else "mpeg"
                            if not mediasetRes[k]["url"]:
                                mediasetRes[k]["isWidevine"] = "widevine" in key["assetTypes"]
                                mediasetRes[k]["pid"] = key["releasePids"][0]
                                mediasetRes[k]["url"] = key["publicUrls"][0]
                    except:
                        logger.error(f"No PublicUrls for '{title}' with format {strmFormat}")

                if mediasetRes["dash"]["url"] and mediasetRes["mpeg"]["url"]:
                    break

    items = item = key = None
    
    url = mediasetRes["mpeg"]["url"]

    if not url: 
        forceMpd = True
        url = mediasetRes["dash"]["url"]
        widevine = mediasetRes["dash"]["isWidevine"]
        pid = mediasetRes["dash"]["pid"]

    if "theplatform" in url:
        url = requests.get(url, headers=headers).url

    if url:
        if forceMpd:
            res.ManifestType = "mpd"
            res.ManifestUpdateParameter = "full"
            if widevine and pid:
                res.LicenseKey = LICENSE_URL.format(pid=pid, token=token)
        
        url = f"{url}|user-agent={utils.USER_AGENT}" #kodi 19 compatibility
        res.StreamHeaders = f"user-agent={utils.USER_AGENT}"
        res.Url = url
    else:
        logger.error("No url found for: ", search)
    
    return res


def play_02(search):
    res = BroadcasterResult()

    url = ""
    pid = ""
    callSign = ""

    # search
    if search.startswith("$"): 
        callSign = search[1:]
    else:
        items = requests.get(ALLSTATION_URL).json()["entries"]
        for item in items:
            if search.startswith("$"):
                _search = "$" + item["callSign"]
            else:
                _search = item["title"]

            if item.get("tuningInstruction", "") and _search == search:
                callSign = item["callSign"]
                break
        items = None

    item = requests.get(ALL_JSON).json()["response"]["listings"][callSign]

    item["nextListing"] = None
    item["currentListing"]["description"] = ""
    item["currentListing"]["mediasetlisting$epgTitle"] = ""
    item["currentListing"]["program"]["tags"] = None
    item["currentListing"]["program"]["title"] = ""
    item["currentListing"]["program"]["mediasetlisting$epgTitle"] = ""
    item["currentListing"]["program"]["description"] = None
    item["currentListing"]["program"]["longDescription"] = None
    item["currentListing"]["program"]["mediasetprogram$longDescriptionUI"] = None
    item["currentListing"]["program"]["mediasetprogram$tvLinearSeasonTitle"] = None
    item["currentListing"]["program"]["mediasetprogram$brandDescriptionUI"] = None
    item["currentListing"]["program"]["thumbnails"] = None

    publicUrl = item["publicUrl"]
    restartUrl = "" if "restartUrl" not in item["currentListing"] else item["currentListing"]["restartUrl"] 

    jsonStreamRequestData = {
        "channelCode":f"{callSign}",
        "streamType":"LIVE",
        "delivery":"Streaming",
        "createDevice":"true",
        "overrideAppName": appName
    }

    headersStreamRequest = {"Authorization": f"Bearer {token}", "User-Agent": utils.USER_AGENT}
    jsonStream = requests.post(STREAM_URL.format(sid=sid), json=jsonStreamRequestData, headers=headersStreamRequest).json()
    
    jsonUrlComposer = jsonStream["response"]["mediaSelector"]
    parameters = {x: jsonUrlComposer[x] for x in jsonUrlComposer if x not in ["url", "format", "formats"]}
    parameters["format"]  = "SMIL"
    parameters["formats"] = "MPEG-DASH,MPEG4,M3U"
    parameters["auth"] = token

    itemUrl = publicUrl if restartUrl == "" else restartUrl
    smilUrl = f"{itemUrl}?" + urlencode(parameters)
    smilXml = requests.get(smilUrl).content.decode()

    xml = xmltodict.parse(smilXml)
    ref = xml["smil"]["body"]["seq"]["switch"]["ref"]
    par = ref["param"]
    url = ref["@src"] 
    
    isEncrypted = False if not "@security" in ref else ref["@security"] == "commonEncryption"
    pid = scrapers.findSingleMatch(par["@value"], r"\|pid=([^|]+)")

    if url:
        # set manifest for IA
        res.ManifestType = "hls"

        if mpd:
            res.ManifestType = "mpd"
            res.ManifestUpdateParameter = "full"
            if isEncrypted and pid:
                res.LicenseKey = LICENSE_URL.format(pid=pid, token=token)
        
        url = f"{url}|user-agent={utils.USER_AGENT}" #kodi 19 compatibility
        res.StreamHeaders = f"user-agent={utils.USER_AGENT}"
        res.Url = url
    else:
        logger.error("No url found for: ", search)
    
    return res


def play_01(search):
    res = BroadcasterResult()

    url = ""
    pid = ""
    callSign = ""

    formats = "MPEG-DASH" if mpd else "M3U"
    strmFormat = "dash+xml" if mpd else "x-mpegURL"

    # get Json
    items = requests.get(ALLSTATION_URL).json()["entries"]

    # search
    if search.startswith("$"):
        search = search.replace("$", "")
        callSign = search
    else:
        for item in items:
            if search.startswith("$"):
                _search = "$" + item["callSign"]
            else:
                _search = item["title"]

            if item.get("tuningInstruction") and _search == search:
                for key in item["tuningInstruction"]["urn:theplatform:tv:location:any"]:
                    if key["format"] == "application/{}".format(strmFormat):
                        try:
                            if mpd and "widevine" in key["assetTypes"] and "geoIT" in key["assetTypes"]:
                                pid = key["releasePids"][0]
                                break
                            elif not mpd:
                                break
                        except:
                            logger.error(f"No PublicUrls for {search} with format {strmFormat}")
                callSign = item["callSign"]
                break

    jsonStreamRequestData = {
        "channelCode":f"{callSign}",
        "streamType":"LIVE",
        "delivery":"Streaming",
        "createDevice":"true",
        "overrideAppName": appName
    }

    headersStreamRequest = {"Authorization": f"Bearer {token}", "User-Agent": utils.USER_AGENT}
    jsonStream = requests.post(STREAM_URL.format(sid=sid), json=jsonStreamRequestData, headers=headersStreamRequest).json()
    
    urlComposer = jsonStream["response"]["mediaSelector"]
    
    parameters = {}
    parameters = {x: urlComposer[x] for x in urlComposer if x not in ["url", "formats"]}
    parameters["formats"] = formats
    parameters["auth"] = token

    itemUrl = urlComposer["url"]
    smilUrl = f"{itemUrl}?" + urlencode(parameters)
    smilXml = requests.get(smilUrl).content.decode()

    xml = xmltodict.parse(smilXml)
    url = xml["smil"]["body"]["seq"]["switch"]["video"]["@src"]

    if url:
        # set manifest for IA
        res.ManifestType = "hls"

        if mpd:
            res.ManifestType = "mpd"
            res.ManifestUpdateParameter = "full"
            if pid:
                res.LicenseKey = LICENSE_URL.format(pid=pid, token=token)
        
        url = f"{url}|user-agent={utils.USER_AGENT}" #kodi 19 compatibility
        res.StreamHeaders = f"user-agent={utils.USER_AGENT}"
        res.Url = url
    else:
        logger.error("No url found for: ", search)
    
    return res
