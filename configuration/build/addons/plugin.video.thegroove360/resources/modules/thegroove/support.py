from resources.lib import kodiutils
import os
import logging
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import sys
import subprocess
from resources.modules.httpclient import HttpClient

logger = logging.getLogger(xbmcaddon.Addon().getAddonInfo('id'))


def panel_list(url, wait=500):
    skip = kodiutils.get_setting_as_bool("check_liste")
    if skip:
        return None

    import re
    # url_ori = url
    try:
        url = url.split(";")[0]
        if url.startswith('/thegroove/'):
            from resources.modules.thegroove.thegroove_httpclient import ThegrooveHttpClient
            httpclient = ThegrooveHttpClient()
        else:
            httpclient = HttpClient()

        try:
            base_url = re.compile(r'(http.*?://.*?/)').findall(url)[0]
        except:
            base_url = None
        try:
            username = re.compile(r'username=(.*?)(?:&|$)').findall(url)[0]
        except:
            username = None
        try:
            password = re.compile(r'password=(.*?)(?:&|$)').findall(url)[0]
        except:
            password = None
        try:
            l_type = re.compile(r'type=(.*?)(?:&|$)').findall(url)[0]
        except:
            l_type = None

        if (url.startswith('http') or (url.startswith('/thegroove/'))) and not l_type and (
                l_type != "m3u" or l_type != "m3u8"):

            r = httpclient.get_request(url, timeout=1)

            if url.startswith('http'):
                if r.status_code > 399:
                    return None
                lista = r.content
            else:
                lista = r
            
            expr = r'(http.*?//(.*?/).*?)/([\d|\d\.ts|\d\.m3u8]+)\s'
            matches = re.compile(expr, re.MULTILINE).findall(lista)

            match = matches[0][0]
            if match:
                url = match.replace("/live/", "/")
                print(url)
                expr = r'(http.*?://.*?:[\d]+/)(.*?)/(.*?)$'
                matches = re.compile(expr, re.IGNORECASE).findall(url)[0]
                base_url = matches[0]
                username = matches[1]
                password = matches[2]
                l_type = "m3u"

        if base_url and username and password and l_type:
            panel_url = base_url + "player_api.php?username=" + username + "&password=" + password + "&"

            xbmc.sleep(wait)
            r = HttpClient().get_request(panel_url, timeout=1)

            logger.debug(r.status_code)
            logger.debug(r.text)

            if r.status_code > 399:
                return None
            info = r.json()["user_info"]

            import datetime
            try:
                expires = datetime.datetime.fromtimestamp(float(info["exp_date"])).strftime("%d/%m/%Y")
            except Exception:
                # print e.message
                expires = "-"

            return [str(info["status"]), str(info["active_cons"]), str(info["max_connections"]), str(info["auth"]),
                    expires]

    except Exception as e:
        if kodiutils.get_setting_as_bool("debug"):
            import traceback
            traceback.print_stack()
            logger.debug(str(e))
        return None


def mac_list_check(url, wait=2000):
    from resources.modules.thegroove.portal_api import PortalApi
    import re
    try:
        portal = PortalApi(url)
        url = portal.get_link("ffmpeg%20http://localhost/ch/1823_&series=")
        logger.debug(url)
        try:
            url = url.split(" ")[1]
        except:
            pass

        expr = r'(http.*?://.*?:[\d]+/)(.*?)/(.*?)/.*?$'
        matches = re.compile(expr, re.IGNORECASE).findall(url)[0]
        base_url = matches[0]
        username = matches[1]
        password = matches[2]
        l_type = "m3u"

        url = base_url + "get.php?username=" + username + "&password=" + password + "&type=" + l_type

        return panel_list(url, wait)
    except Exception as e:
        import traceback
        traceback.print_stack()
        logger.debug(e)
        pass


def get_cores_num():
    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except ImportError:
        pass

    try:
        res = open('/proc/cpuinfo').read().count('processor\t:')

        if res > 0:
            return res
    except IOError:
        pass

    try:
        res = int(os.environ['NUMBER_OF_PROCESSORS'])

        if res > 0:
            return res
    except (KeyError, ValueError):
        pass

    try:
        try:
            dmesg = open('/var/run/dmesg.boot').read()
        except IOError:
            dmesg_process = subprocess.Popen(['dmesg'], stdout=subprocess.PIPE)
            dmesg = dmesg_process.communicate()[0]

        res = 0
        while '\ncpu' + str(res) + ':' in dmesg:
            res += 1

        if res > 0:
            return res
    except OSError:
        pass
    return 2


def transliterate(text):
    try:
        from resources.lib.pytils import translit
        # from resources.lib.pytils.third import six
        ttext = translit.translify(text, False)

        return ttext
    except Exception as e:
        if kodiutils.get_setting_as_bool("debug"):
            import traceback
            traceback.print_exc()
            logger.debug(str(e))
        return text


def cleanup():
    import shutil
    from resources.modules.thegroove.thegroove_httpclient import ThegrooveHttpClient
    req = HttpClient().get_request(ThegrooveHttpClient().server_url + "/Thepasto/remove.php")
    json_data = req.json()

    dDialog = xbmcgui.DialogProgress()
    dDialog.create(xbmcaddon.Addon().getAddonInfo('name'), "Rimozione In Corso:")

    for i, r in enumerate(json_data):
        perc = int((i + 1) * 100 / len(json_data))
        dDialog.update(perc, "Rimozione id " + r + " " + str(i + 1) + " di " + str(len(json_data)) + "Kb")
        for p in ["profile/addon_data/", "home/addons/"]:
            p.replace("/", os.sep)
            if sys.version_info[0] > 2:
                pr = xbmcvfs.translatePath(os.path.join("special://", p, r))
            else:
                pr = xbmc.translatePath(os.path.join("special://", p, r))

            if os.path.isdir(pr):
                try:
                    shutil.rmtree(pr, ignore_errors=False)
                except:
                    pass

    dDialog.close()


def get_version():
    import xml.etree.ElementTree as ET
    if sys.version_info[0] > 2:
        root = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('Path'))
    else:
        root = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('Path'))
    addon = os.path.join(root, "addon.xml")

    root = ET.parse(open(os.path.join(addon), "r")).getroot()
    return root.attrib["version"]


def get_revision(attr):
    import json
    if sys.version_info[0] > 2:
        root = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('Path'))
    else:
        root = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('Path'))
    with open(os.path.join(root, 'thegroove_version.json'), 'r') as f:
        version = json.load(f)
        f.close()

    return version[attr]


def get_zeronet_page(page):
    if page.startswith("http://127.0.0.1:43110"):
        zurl = kodiutils.get_setting("zeronet_url")
        if zurl and zurl != "":
            page = page.replace("http://127.0.0.1:43110", "http://" + zurl)

    return page
