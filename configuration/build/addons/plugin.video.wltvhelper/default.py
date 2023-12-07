import xbmcplugin
import routing
import requests
import importlib

from xbmcaddon import Addon
from lib.broadcaster_result import BroadcasterResult
from lib.install import install 
from lib import logger, config, utils, player

plugin = routing.Plugin()

####
# Starting point: the first page appearing to User
####
@plugin.route("/")
def start():
    handle = plugin.handle
    if not utils.checkSetup(): return
    utils.checkSettings()
    config.cleaunUpSettings()

    # Compose "MAKER" listitem
    utils.addMenuItem(handle, 30010, plugin.url_for(maker), icon="compose")

    # Compose "SWITCHER" listitem
    utils.addMenuItem(handle, 30002, plugin.url_for(switch), icon="list")

    # Compose "Internal TV" listitem
    if config.getSetting("internalListNavigation") == True:
        utils.addMenuItem(handle, 30177, plugin.url_for(wltvlist), icon="tv")

    # Compose "Internationals TV" listitem
    utils.addMenuItem(handle, 30126, plugin.url_for(worldtv), icon="globe")

    # Compose "United Music Radio" listitem
    utils.addMenuItem(handle, 30127, plugin.url_for(unitedmusic), icon="unitedmusic_xs", thumb="unitedmusic", fanart="unitedmusic")

    # Compose "International Radios" listitem
    utils.addMenuItem(handle, 30159, plugin.url_for(worldradio), icon="globe")

    # Compose "SkyLine WebCam" listitem
    utils.addMenuItem(handle, 30128, plugin.url_for(skylinewebcams), icon="webcam")

    # Compose "YouTube Music & Karaoke" listitem
    utils.addMenuItem(handle, 30149, plugin.url_for(youtubemusic), icon="youtube")

    # Compose "Player List VOD Manager" listitem
    utils.addMenuItem(handle, 30141, plugin.url_for(listvodmanager), icon="compose")

    # Compose "SETTINGS" listitem
    utils.addMenuItem(handle, 30003, plugin.url_for(setting), icon="settings")

    # Compose "SEND LOG" listitem
    utils.addMenuItem(handle, 30122, plugin.url_for(uploadLog), icon="log", isFolder=False)

    # Compose "FORCE UPDATE"
    strMsg = utils.getCurrentVersionAndHotfixString()
    utils.addMenuItem(handle, strMsg, plugin.url_for(forceCheckUpdate), icon="log", isFolder=False)

    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)


####
# Open Internals TV section
###
@plugin.route("/wltvlist")
@plugin.route("/wltvlist/<code>")
def wltvlist(code=""):
    from lib import wltvlist
    wltvlist


####
# Open UnitedMusic
###
@plugin.route("/unitedmusic")
@plugin.route("/unitedmusic/showstations/<name>/<code>")
def unitedmusic(name="", code=""):
    from lib import unitedmusic
    unitedmusic


####
# Open Internationals TV section
###
@plugin.route("/worldtv")
@plugin.route("/worldtv/showcountries/<continentcode>")
@plugin.route("/worldtv/switchlist/<name>/<code>")
def worldtv(continentcode="", name="", code=""):
    from lib import worldtv
    worldtv


####
# Open Internationals Radios section
###
@plugin.route("/worldradio")
@plugin.route("/worldradio/showcities/<countrycode>")
@plugin.route("/worldradio/showradios/<countrycode>/<citycode>")
def worldradio(countrycode="", citycode=""):
    from lib import worldradio
    worldradio


####
# Open SkyLineWebCams
###
@plugin.route("/skylinewebcams")
@plugin.route("/skylinewebcams/showcountries/<continentcode>")
@plugin.route("/skylinewebcams/showregion/<continentcode>/<countrycode>")
@plugin.route("/skylinewebcams/showcities/<continentcode>/<countrycode>/<regioncode>")
@plugin.route("/skylinewebcams/showwebcams/<continentcode>/<countrycode>/<regioncode>/<citycode>")
def skylinewebcams(continentcode="",countrycode="",regioncode="",citycode=""):
    from lib import skylinewebcams
    skylinewebcams


####
# Open YouTube Music & Karaoke
###
@plugin.route("/youtubemusic")
@plugin.route("/youtubemusic/showchannels/<group>")
@plugin.route("/youtubemusic/showvideos/<name>/<code>")
def youtubemusic(name="",code="",group=""):
    from lib import youtubemusic
    youtubemusic


####
# Open Player List VOD Manager
###
@plugin.route("/vodmanager")
@plugin.route("/vodmanager/showchoice/<itemId>")
@plugin.route("/vodmanager/showchoice/<itemId>/<streamType>")
@plugin.route("/vodmanager/showgroups/<itemId>/<streamType>/<subGroup>/<searchType>")
@plugin.route("/vodmanager/showgroups/<itemId>/<streamType>/<subGroup>/<searchType>/<txtSearch>")
@plugin.route("/vodmanager/globalsearch/<streamType>")
@plugin.route("/vodmanager/showsearch/<itemId>/<streamType>")
@plugin.route("/vodmanager/showfiltered/<itemId>/<streamType>/<subGroup>/<txtSearch>/<isUserSearch>")
def listvodmanager(itemId="", streamType="", subGroup="", searchType="", txtSearch="", isUserSearch=False):
    from lib import listvodmanager
    listvodmanager


####
# Start playing importing broadcaster module
####
@plugin.route("/play/<broadcaster>/<channel>")
def play(broadcaster, channel): #, userAgent=None):
    player.play(broadcaster, channel)


####
# Open YouTube & start play
####
@plugin.route("/play/yt/<chtype>/<id>")
@plugin.route("/play/yt/<chtype>/<id>/<chname>")
def playYT(chtype, id, chname=""):
    c = importlib.import_module(f"broadcaster.yt")
    res = c.play(chtype,id,chname)
    player.makeListItemToPlay(res)


@plugin.route("/play/<broadcaster>/<channel>/<listName>/<groupId>/<channelId>")
def playFromTvChannels(broadcaster, channel, listName, groupId, channelId):
    userAgent = None
    userAgentIdx = channelId.find("|User")
    if userAgentIdx > -1:
        logger.debug(f"{channelId} has user agent! Removing")
        userAgent = channelId[userAgentIdx + 1:]  # get the UA removing `|`
        channelId = channelId[0:userAgentIdx]
        logger.debug("UserAgent is:", userAgent)

    logger.debug(f'Requested channel for play: "{broadcaster}" "{channel}" "{listName}" "{groupId}" "{channelId}"')

    forceDirectLink = config.getSetting("forceDirectLink")

    hasBroadcaster = broadcaster != "none" and broadcaster != "none/none"

    logger.debug(f"Requested link hasBroadcaster: {hasBroadcaster} - forceDirectLink: {forceDirectLink}")

    if hasBroadcaster and not forceDirectLink:
        # forward request to `play()`
        play(broadcaster, channel) #, userAgent)
    else:
        logger.debug("No broadcaster requested or forceDirectLink, proceed with tvchannels")
        # no broadcaster has been requested: proceed forwarding request to tvchannels.
        # Use `list_name`, `group_id` and `chl_id`

        apiKeyParameter = utils.getApikeyParameter()
        url = f"{utils.API_DOMAIN}/{listName}/live?{apiKeyParameter}channel={channelId}&group={groupId}"
        logger.debug("The initial url is: ", url)

        finalUrl = check_url_redirect(url)
        logger.debug("The final url is: ", finalUrl)
        if not finalUrl:
            raise "No redirect url found"

        bdcRes = BroadcasterResult()
        bdcRes.Url = finalUrl

        player.makeListItemToPlay(bdcRes, userAgent)


@plugin.route("/webcam/<broadcaster>/<country>/<region>/<city>/<part>")
def playWebcam(broadcaster, country, region, city, part):
    linkWebCam = f"{country}/{region}/{city}/{part}"
    play(broadcaster, linkWebCam)


####
# Start installing additional/required addons
####
@plugin.route("/install")
def installDeps():
    install()


####
# Switch between iptv lists.
# This method compute the 'tvchannels-url' and put it into PVR Simple Client settings
####
@plugin.route("/switch")
def switch():
    from lib import switcher
    switcher


####
# Open the XML windows in order to compose a personal IPTV list (using 'tvchannels-merge' function)
###
@plugin.route("/maker")
def maker():
    from lib import userlistmaker
    userlistmaker.launch()


####
# Open addon's settings
####
@plugin.route("/settings")
def setting():
    config.openSettings()


####
# Open Input Helper addon's settings
####
@plugin.route("/openinputhelper")
def openInputStreamHelper():
    inputStreamHelper = Addon("script.module.inputstreamhelper")
    inputStreamHelper.openSettings()


####
# Open Input Helper addon's settings
####
@plugin.route("/chooserai3region")
def chooseRai3Region():
    from broadcaster import rai
    rai.chooseRai3Region()


####
# Cleanup cache files
####
@plugin.route("/cachecleanup")
def cacheCleanup():
    utils.cacheCleanup()


####
# Force check update
####
@plugin.route("/forcecheckupdate")
def forceCheckUpdate():
    utils.forceCheckUpdate()


####
# Force hotfix apply
####
@plugin.route("/forcehotfix")
def forceHotfix():
    utils.forceCheckUpdate(True)


####
# Send log file
####
@plugin.route("/uploadlog")
def uploadLog():
    logger.info(f"WLTV {utils.getCurrentVersionAndHotfixString()}")
    from lib import loguploader, listmanager
    repl = listmanager.getUserListUrls()
    loguploader.Main(repl)


def check_url_redirect(url):
    resp = requests.get(url, allow_redirects=False)
    if resp.status_code > 299 and resp.status_code < 304:
        # redirect url
        redirect = resp.headers["Location"]
        if redirect.startswith("plugin://"):
            logger.debug("URL points to plugin, follow!")
            return redirect
    return url


# start router
utils.checkForUpdates()

plugin.run()
