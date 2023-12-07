# -*- coding: utf-8 -*-

import routing
import logging
import xbmcaddon
import xbmcgui
import xbmc
import xbmcvfs
import json
import base64
import os
import re
import sys

from resources.modules.thegroove.epg_light import EpgLight

try:
    from urllib.parse import quote as quoter
    from urllib.parse import unquote as unquoter
    from urllib.parse import urlparse
    from urllib.parse import parse_qs
except ImportError:
    from urllib import quote as quoter
    from urllib import unquote as unquoter
    from urlparse import urlparse as urlparse
    from urlparse import parse_qs as parse_qs

from resources.lib import kodilogging
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setResolvedUrl
from resources.modules import item_parser
from resources.modules.thegroove.thegroove_httpclient import ThegrooveHttpClient as TGHttpClient
from resources.modules.httpclient import HttpClient as HttpClient
from resources.modules.thegroove.thegroove_item import ThegrooveItem
from resources.modules.thegroove.local import LocalItem
from resources.modules.thegroove import thegroove_resolvers
from resources.lib import kodiutils

from resources.modules.thegroove.acestream_http_api import AcestreamHttpApi
from resources.modules.thegroove.thegroove_player import TheGroovePlayer

import resources.modules.thegroove.updater as updater
from resources.modules.thegroove import support

ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()
stop_playing_thread = False


@plugin.route('/')
def index():
    if not kodiutils.get_setting_as_bool("skipintro") and not kodiutils.get_setting_as_bool("intro_viewed"):
        tg_item = ThegrooveItem()
        tg_item.label = "Intro Thegroove 360"
        tg_item.url = TGHttpClient().server_url + "mariobrossvideo/intro.mp4"
        tg_item.is_folder = False
        tg_item.is_playable = True
        ser_item = base64.b64encode(json.dumps(tg_item, default=ThegrooveItem.convert_to_dict).encode("utf-8"))
        kodiutils.set_setting("intro_viewed", "true")
        return play_item(ser_item)

    kodiutils.set_setting("intro_viewed", "false")
    updater.check_update()
    kodiutils.set_setting("n_cores", 0)
    set_router('/thegroove/ingresso')


@plugin.route('/dialog/<path:sitem>')
def show_dialog(sitem):
    logger.debug("____________ SHOW DIALOG ____________")
    b64_item = base64.b64decode(sitem)
    item = json.loads(b64_item)
    tg_item = ThegrooveItem.dict_to_obj(item)

    dialog = xbmcgui.Dialog()
    lis = []

    for c, subls in enumerate(tg_item.sublinks):
        name = subls[0]
        link = subls[1]
        if link == "":
            continue
        name = str((c + 1)) + " - " + name if name != "" else str((c + 1)) + " - " + "Link"
        li = ListItem(name)
        li.setArt(tg_item.arts)
        lis.append(li)

    ret = dialog.select(tg_item.label, lis)
    if ret > -1:
        tg_item.url = tg_item.sublinks[ret][1]
        tg_item._raw = re.compile(r'(<sublink.*?>.*?</sublink>)', re.MULTILINE).findall(tg_item._raw)[ret]
        tg_item.is_folder = False
        tg_item.tg_resolver = tg_item.sublinks[ret][2]
        if sys.version_info[0] > 2:
            ser_item = base64.b64encode(json.dumps(tg_item, default=ThegrooveItem.convert_to_dict).encode()).decode()
        else:
            ser_item = base64.b64encode(json.dumps(tg_item, default=ThegrooveItem.convert_to_dict))
        play_item(ser_item)


@plugin.route('/regex/<path:sitem>')
def do_regex(sitem):
    logger.debug("____________ DO REGEX ____________")
    b64_item = base64.b64decode(sitem)
    item = json.loads(b64_item)

    # logger.debug(b64_item)

    tg_item = ThegrooveItem.dict_to_obj(item)
    parser = item_parser.ItemParser()
    page = parser.parse_regex(tg_item)

    if parser.repeat_mode == "single" and parser.regex_mode == "python":
        if tg_item.is_playable:
            tg_item.url = page
            if sys.version_info[0] > 2:
                ser_item = base64.b64encode(
                    json.dumps(tg_item, default=ThegrooveItem.convert_to_dict).encode()).decode()
            else:
                ser_item = base64.b64encode(json.dumps(tg_item, default=ThegrooveItem.convert_to_dict))
            return play_item(ser_item)
        else:
            set_router(page)
    if parser.repeat_mode == "repeat" and parser.regex_mode == "python":
        set_router(itemlist=parser.page_list)
    if parser.repeat_mode == "repeat" and parser.regex_mode == "regex":
        set_router(itemlist=parser.page_list)


@plugin.route('/play/<path:sitem>')
def play_item(sitem):
    logger.debug("____________ PLAY ____________")
    xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    b64_item = base64.b64decode(sitem)
    item = json.loads(b64_item)
    ste_item = ThegrooveItem.dict_to_obj(item)

    pl_th = None

    # logger.debug(item)
    logger.debug(ste_item.url)

    listitem = xbmcgui.ListItem(ste_item.label, ste_item.label)
    # thumb = ste_item.arts["thumb"] if "thumb" in ste_item.arts else ""
    listitem.setInfo("video", infoLabels=ste_item.info)
    listitem.setArt(ste_item.arts)

    play_url = ste_item.url
    play_label = ste_item.label
    listitem.setProperty('IsPlayable', 'true')

    if ste_item.tg_resolver == "":
        tg_res = ste_item.get_thegroove_resolver(ste_item._raw, play_url)
    else:
        tg_res = ste_item.tg_resolver

    if tg_res != "":
        ste_item.tg_resolver = tg_res

    if ste_item.tg_resolver == "":
        if "plugin://" not in ste_item.url:
            play_url = get_resolved(play_url)
        else:
            play_url = play_url.replace("&amp;", "&")
    else:
        # logger.debug(ste_item.tg_resolver)

        if ste_item.tg_resolver == "f4m":
            play_label, play_url = thegroove_resolvers.f4m(play_label, play_url)
        elif ste_item.tg_resolver == "resolve":
            play_url = get_resolved(play_url)
        elif ste_item.tg_resolver == "tltv":
            play_url = thegroove_resolvers.get_tl_tv(play_url)
        elif ste_item.tg_resolver == "dbstr":
            play_url = thegroove_resolvers.db_strm(play_url)
        else:
            play_label = play_label.encode("ascii", "ignore")
            if ste_item.tg_resolver == "tor":
                if "magnet%3A%" not in play_url:
                    play_url = quoter(play_url)
            play_url = thegroove_resolvers.resolvers[ste_item.tg_resolver].format(play_url, play_label)

    ste_item.label = play_label
    xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

    if play_url is None:
        return

    if "plexus" in play_url:
        logger.debug(play_url)
        play_url = re.compile(r'url=([^&]+)', re.MULTILINE).findall(play_url)[0]
        ste_item.tg_resolver = "ace"

    if ste_item.tg_resolver == "ace" and not kodiutils.get_setting_as_bool("use_plexus"):
        ace_api = AcestreamHttpApi()
        ace_api.get_stream_url(thegroove_resolvers.ace_hash(play_url))
        if not ace_api.playback_url:
            return
        else:
            logger.debug(ace_api)
            tgp = TheGroovePlayer()
            tgp.set_ace_api(ace_api)
            tgp.play(ace_api.stream_url, listitem)
            ace_api.pb_dialog.create(xbmcaddon.Addon().getAddonInfo('name'), "")
            ace_api.show_stats()

            while tgp.is_active:
                if int(xbmc.getCondVisibility('Window.IsActive(videoosd)')) > 0:
                    tgp.overlay.show()
                    r = ace_api.get_stats()
                    logger.debug("---------------------------------------------------------")
                    logger.debug(r)
                    if r["response"]:
                        tgp.overlay.set_information(r["response"])
                    xbmc.sleep(1000)
                else:
                    if tgp.overlay.showing:
                        tgp.overlay.hide()

                tgp.sleep(100)

            setResolvedUrl(plugin.handle, True, listitem=listitem)
            return

    logger.debug("------------------------------------")
    logger.debug(play_url)
    logger.debug("------------------------------------")
    try:
        stream_url, headers = play_url.split("|")

    except:
        stream_url = play_url
        headers = ""

    if "f4mTester" in play_url:
        # xbmc.executebuiltin("RunPlugin(" + play_url + ")")
        parsed = urlparse(play_url)
        link = parse_qs(parsed.query)['url'][0]
        streamtype = parse_qs(parsed.query)['streamtype'][0]

        try:
            ste_item.label = ste_item.label.split("[CR]")[0]
        except:
            pass

        import threading

        if kodiutils.get_setting_as_bool("show_epg"):
            global stop_playing_thread
            from resources.modules.thegroove.epg import Epg
            epg = Epg()
            epg.set_channels_names()
            pl_th = threading.Thread(target=is_playing, args=(ste_item, epg))
            pl_th.start()

        from resources.modules.thegroove.thegroove_f4m_helper import TGf4mProxyHelper
        TGf4mProxyHelper().playF4mLink(link, ste_item, streamtype=streamtype, use_proxy_for_chunks=True)
    else:
        if "GreenTorrent" in play_url:
            if "magnet%3A%" not in play_url:
                parsed = urlparse(play_url)
                magnet = quoter(parse_qs(parsed.query)['url'][0])
                play_url = thegroove_resolvers.resolvers["tor"].format(magnet, play_label)
            play_url += "|!User-Agent=%s" % quoter("VLC/3.0.9 LibVLC/3.0.9")

        if stream_url.endswith(".mpd") or "force_inputstream" in headers:
            listitem.setContentLookup(False)
            listitem.setMimeType('application/xml+dash')
            listitem.setProperty('inputstream', 'inputstream.adaptive')
            listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            hs = headers.replace("!", "").split("&")
            isa_headers = ""
            isa_lic_url = ""
            for h in hs:
                if h == '':
                    continue
                hk, hv = h.split("=", 1)
                if hk == "isa_license_url":
                    isa_lic_url = hv
                    continue
                if hk != "force_inputstream":
                    isa_headers += hk + "=" + unquoter(hv) + "&"
            listitem.setProperty('inputstream.adaptive.manifest_headers', isa_headers.strip("&"))
            # listitem.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            if isa_lic_url != "":
                listitem.setProperty('inputstream.adaptive.license_key', isa_lic_url)
            play_url = stream_url

        xbmc.Player().play(play_url, listitem)

    stop_playing_thread = True
    if pl_th:
        pl_th.join()

    setResolvedUrl(plugin.handle, True, listitem=listitem)


def is_playing(sitem, epg):
    global stop_playing_thread
    while stop_playing_thread is False:

        is_seekbar = int(xbmc.getCondVisibility('Window.IsActive(seekbar)')) > 0

        if xbmc.getCondVisibility('Player.HasVideo') and is_seekbar:

            try:
                sitem.label = sitem.label.split("[CR]")[0]
            except:
                pass

            info = epg.find_current_playing(sitem.label)
            # logger.debug(sitem.label)
            # logger.debug(info)
            if info != "":
                sitem = epg.format_info(info, sitem)

            item = xbmcgui.ListItem()
            item.setPath(xbmc.Player().getPlayingFile())
            item.setInfo("video", infoLabels=sitem.info)
            item.setArt(sitem.arts)
            xbmc.Player().updateInfoTag(item)

        xbmc.sleep(5000)


@plugin.route('/thegroove/<path:page>')
def show_category_thegroove(page):
    logger.debug("__________ SHOW CATEGORY THEGROOVE ____________")
    page = unquoter(page)

    if "scripters/" in page and "path=" in page:
        scripter, spage = page.replace("scripters/", "").split("/")
        page = "php_script_loader?scripter=" + unquoter(scripter) + "&" + unquoter(spage)
    set_router("/thegroove/" + page)


@plugin.route('/ext/<path:page>')
def show_category(page):
    logger.debug("__________ SHOW CATEGORY ____________")
    set_router(page)


@plugin.route('/plugin/<path:plugin_url>')
def open_plugin(plugin_url):
    logger.debug("__________ OPEN PLUGIN ____________")
    plugin_url = unquoter(plugin_url)
    xbmc.executebuiltin('Dialog.Close(busydialog)')
    xbmc.executebuiltin("ActivateWindow(music, " + plugin_url + ", return)")


@plugin.route('/thegroove/scripters/<scripter>/<path:page>')
def show_scripters_page(scripter, page):
    logger.debug("__________ SHOW CATEGORY SCRIPTERS ____________")
    url_page = "php_script_loader?scripter=" + unquoter(scripter) + "&" + unquoter(page)
    show_category_thegroove(url_page)


def get_resolved(url):
    import resolveurl
    xxx_plugins_path = 'special://home/addons/script.module.resolveurl.xxx/resources/plugins/'
    if xbmcvfs.exists(xxx_plugins_path):
        if sys.version_info[0] > 2:
            xxxp = xbmcvfs.translatePath(xxx_plugins_path)
        else:
            xxxp = xbmc.translatePath(xxx_plugins_path)
        resolveurl.add_plugin_dirs(xxxp)
    try:
        resolved = resolveurl.resolve(url)
        if resolved:
            return resolved
        raise
    except Exception as e:
        import resolver_360
        resolved = resolver_360.resolve(url)
        try:
            if type(resolved[0]) is list and len(resolved[0]) > 1:
                dialog = xbmcgui.Dialog()
                labels = []
                for lab in resolved[0]:
                    labels.append(lab[0])
                ret = dialog.select('Links', labels)
                if ret == -1:
                    return None
                if ret >= 0:
                    return resolved[0][ret][1]
            if type(resolved) is list and len(resolved) == 1:
                return resolved[0]
        except:
            pass
        # raise e
    return url


def set_router(page='', itemlist=None):
    logger.debug("________ ROUTER _________")

    logger.debug(page)
    if page == '' and itemlist is None:
        return

    if kodiutils.get_setting_as_bool("show_epg") or kodiutils.get_setting_as_bool("show_logos"):
        import threading
        epg_updater_running = False
        for t in threading.enumerate():
            if t.name == "epg_updater" or t.name == "logos_updater":
                epg_updater_running = True
                break

        if not epg_updater_running:
            updater.epg_logos_update()

    if page == "/thegroove/local":
        return show_local_page()

    if page != "":
        is_tg_page = page.startswith("/thegroove/")

        if is_tg_page:
            page = page.replace("/thegroove/", "")

        if is_tg_page:
            client = TGHttpClient()
        else:
            client = HttpClient()

        page = support.get_zeronet_page(page)
        res = client.get_request(page)

        parser = item_parser.ItemParser()
        if is_tg_page:
            parser.parse_page(res)
        else:
            parser.parse_page(res.text)

        if page.endswith(".m3u"):
            parser.parse_page(thegroove_resolvers.m3u2xml(res.text))

    endOfDirectory(plugin.handle)


def show_item(sitem):
    logger.debug("____________ SHOW ITEM ____________")

    # if show_progress:
    # percent = ((sindex + 1) * 100) / num_items
    # dialog.update(percent, "Elaborando Elementi", "%s di %s" % (sindex + 1, num_items))

    if "f4m" in sitem.url or ThegrooveItem.get_thegroove_resolver(sitem._raw,
                                                                  sitem.url) == "f4m" and not sitem.is_folder:
        from resources.modules.thegroove.epg import Epg
        if kodiutils.get_setting_as_bool("show_epg"):
            epg = Epg()
            info = epg.find_current_playing(sitem.label)
            # logger.debug(info)
            if info != "":
                sitem = epg.format_info(info, sitem)
            else:
                logo = Epg().find_local_logo(sitem.label)
                if logo:
                    sitem.arts["thumb"] = logo
        elif kodiutils.get_setting_as_bool("show_logos"):
            logo = Epg().find_local_logo(sitem.label)
            if logo:
                sitem.arts["thumb"] = logo

    try:
        if sys.version_info[0] > 2:
            ser_item = base64.b64encode(json.dumps(sitem, default=ThegrooveItem.convert_to_dict).encode()).decode()
        else:
            ser_item = base64.b64encode(json.dumps(sitem, default=ThegrooveItem.convert_to_dict))
    except Exception as e:
        if kodiutils.get_setting_as_bool("debug"):
            import traceback
            traceback.print_stack()
            logger.debug(str(e))
        return

    img_folder = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'images')
    li = ListItem(sitem.label, sitem.label)

    if "thumb" not in sitem.arts:
        sitem.arts["thumb"] = ""

    if sitem.arts["thumb"] != "":
        sitem.arts["banner"] = sitem.arts["thumb"]
        sitem.arts["poster"] = sitem.arts["thumb"]
        sitem.arts["icon"] = sitem.arts["thumb"]

    if sitem.arts["fanart"] != "":
        sitem.arts["banner"] = sitem.arts["fanart"]

    if sitem.arts["thumb"] == "":
        sitem.arts["thumb"] = os.path.join(img_folder, "dot_S.png")
        sitem.arts["fanart"] = os.path.join(img_folder, "empty.png")
        sitem.arts["banner"] = os.path.join(img_folder, "empty.png")
        sitem.arts["poster"] = os.path.join(img_folder, "empty.png")

    if sitem.label.strip() == "":
        sitem.arts["thumb"] = os.path.join(img_folder, "empty.png")
        sitem.arts["icon"] = os.path.join(img_folder, "empty.png")

    li.setArt(sitem.arts)
    sitem.info["title"] = sitem.label

    li.setInfo("video", infoLabels=sitem.info)
    # logger.debug(sitem.label + " => " + sitem.url)

    if sitem.url == "" and len(sitem.sublinks) == 0:
        router_url = None
        sitem.is_folder = False
    elif sitem.url.startswith("/thegroove/scripters/"):
        router_url = plugin.url_for(show_scripters_page, quoter(sitem.url.replace("/thegroove/scripters/", "")))
    elif sitem.url.startswith("/thegroove/zeronet"):
        router_url = plugin.url_for(zeronet_update, quoter(sitem.url.replace("/thegroove/zeronet/", "")))
    elif sitem.url.startswith("/thegroove/") and "/scripters/" not in sitem.url:
        router_url = plugin.url_for(show_category_thegroove, quoter(sitem.url.replace("/thegroove/", "")))
    elif sitem.url.startswith("$doregex["):
        router_url = plugin.url_for(do_regex, ser_item)
    elif sitem.is_plugin:
        router_url = plugin.url_for(open_plugin, quoter(sitem.url))
    else:
        if len(sitem.sublinks) > 0 and sitem.url == "" and sitem.is_folder is False:
            router_url = plugin.url_for(show_dialog, ser_item)
        elif sitem.is_folder:
            router_url = plugin.url_for(show_category, sitem.url)
        else:
            router_url = plugin.url_for(play_item, ser_item)

    addDirectoryItem(plugin.handle, router_url, li, sitem.is_folder)


def show_local_page():
    logger.debug("________________ LOCAL PAGE ____________________")
    img_folder = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'images')
    li = ListItem("Aggiungi")
    li.setArt({"thumb": os.path.join(img_folder, "dot_S.png"), "poster": os.path.join(img_folder, "empty.png")})
    router_url = plugin.url_for(show_local_action, action="add", par=None)
    addDirectoryItem(plugin.handle, router_url, li, True)

    local_item = LocalItem()
    local_item.read_json()
    if len(local_item.json_data) > 0:
        for lind, loc in enumerate(local_item.json_data):
            # logger.debug(loc)
            li = ListItem(loc["name"])
            li.setArt({"thumb": os.path.join(img_folder, "dot_S.png"), "poster": os.path.join(img_folder, "empty.png")})
            router_url = plugin.url_for(show_local_action, action="open", par=lind)
            context = local_item.get_context_options(lind)
            # logger.debug(context)
            li.addContextMenuItems(context)
            addDirectoryItem(plugin.handle, router_url, li, True)

    endOfDirectory(plugin.handle)


@plugin.route('/local/<action>/<par>')
def show_local_action(action, par=None):
    logger.debug("________________ LOCAL PAGE ACTION ____________________")
    # logger.debug(action)
    local_item = LocalItem()
    if action == "add":
        jitem_path = ""
        dialog = xbmcgui.Dialog()

        jitem_name = dialog.input('Sceglire Un Nome', type=xbmcgui.INPUT_ALPHANUM)

        if jitem_name != "":
            jitem_path = dialog.browseSingle(1, ADDON.getAddonInfo('name'), '', '.xml')

        if jitem_name != "" and jitem_path != "":
            local_item.read_json()
            if not par == "None":
                local_item.json_data[int(par)]["name"] = jitem_name
                local_item.json_data[int(par)]["path"] = jitem_path
                local_item.write_json()
                return xbmc.executebuiltin("Container.Refresh")
            else:
                local_item.json_data.append({"name": jitem_name, "path": jitem_path})
                local_item.write_json()

    if action == "open":
        if par is None:
            return
        local_item.read_json()
        loc_ite = local_item.json_data[int(par)]
        logger.debug(loc_ite)
        if sys.version_info[0] > 2:
            loc_path = xbmcvfs.translatePath(loc_ite["path"])
        else:
            loc_path = xbmc.translatePath(loc_ite["path"])
        xml_src = local_item.get_local_item_src(loc_path)

        if xml_src:
            parser = item_parser.ItemParser()
            parser.parse_page(xml_src)
            itemlist = parser.page_list
            return set_router("", itemlist)

    if action == "edit":
        if par is None:
            return

        return show_local_action("add", int(par))

    if action == "remove":
        if par is None:
            return

        local_item.read_json()
        local_item.json_data.pop(int(par))
        local_item.write_json()
        return xbmc.executebuiltin("Container.Refresh")


@plugin.route('/cleanup/')
def clean_up():
    from resources.modules.thegroove import support
    support.cleanup()
    dialog = xbmcgui.Dialog()
    dialog.ok(ADDON.getAddonInfo("name"), 'Rimozione Completata')
    return xbmc.executebuiltin("Addon.OpenSettings(" + ADDON.getAddonInfo("id") + ")")


@plugin.route('/update/')
def addon_update():
    updater.check_update()


@plugin.route('/update/<par>')
def check_update(par):
    if par == "epg":
        epg = EpgLight(True, False)
        epg.get_epg_file(force=True)
    elif par == "logos":
        epg = EpgLight(True, False)
        epg.set_logos(force=True)
    elif par == "resolvers":
        updater.resolver_update(force=True)

    return xbmc.executebuiltin("Addon.OpenSettings(" + ADDON.getAddonInfo("id") + ")")


@plugin.route('/zeronet/<par>')
def zeronet_update(par):
    if par == "all":
        updater.zero_update()
    else:
        updater.zero_update(par)

    return xbmc.executebuiltin("Container.Refresh")


def run():
    plugin.run()
