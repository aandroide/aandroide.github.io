import os
import pathlib
import sys
import xbmcaddon
import xbmcvfs
import xbmc
import xbmcgui
import zipfile
import shutil
import logging
import requests
from glob import glob
from resources.lib import kodiutils
import json
import re

from resources.modules.httpclient import HttpClient
from resources.modules.thegroove.epg_light import EpgLight
from resources.modules.thegroove.thegroove_httpclient import ThegrooveHttpClient

try:
    from urllib.parse import quote as quoter
    from urllib.parse import unquote as unquoter
except ImportError:
    from urllib import quote as quoter
    from urllib import unquote as unquoter

logger = logging.getLogger(xbmcaddon.Addon().getAddonInfo('id'))

headers = {'PRIVATE-TOKEN': 'd5xV6QKmNMmaiMNMGijc'}

pDialog = xbmcgui.DialogProgressBG()
dDialog = xbmcgui.DialogProgress()

tg_client = ThegrooveHttpClient()


def get_local_version():
    version_file = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'addon.xml')
    logger.debug(version_file)
    try:
        with open(version_file, 'r') as version_xml:
            v_xml = version_xml.read().encode("utf-8", errors="ignore").decode()
            version = re.compile(r'<addon.*?version=\"([^\"]+)\"\s', re.MULTILINE).findall(v_xml)[0]
            version_xml.close()
            logger.debug("local version: " + version)

            return version
    except Exception as e:
        if kodiutils.get_setting_as_bool("debug"):
            import traceback
            traceback.print_stack()
            logger.debug(e)
        return ""


def get_remote_version():
    global tg_client
    res = requests.get(tg_client.server_url + "zip/addon.xml")
    try:
        version = re.compile(r'<addon.*?version=\"([^\"]+)\"', re.MULTILINE).findall(res.text)[0]
    except:
        version = None

    logger.debug("remote version: " + version)

    return version


def version_tuple(v):
    return tuple(map(int, (v.split("."))))


def zero_update(name=None):
    dDialog = xbmcgui.DialogProgress()
    dDialog.create('Thegroove 360', 'Controllo Aggiornamenti')
    try:

        from resources.lib import websocket

        res = requests.get(tg_client.zeronet_url + "/1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D/",
                           headers={"ACCEPT": "text/html"})
        wrapper_key = re.search('wrapper_key = "(.*?)"', res.text).group(1)

        ws = websocket.create_connection("ws://127.0.0.1:43110/Websocket?wrapper_key=%s" % wrapper_key)
        # ws.send(json.dumps({"cmd": "siteInfo", "params": {}, "id": 1000001})

        requests.get(tg_client.server_url, headers={"ACCEPT": "text/html"})
        # logger.debug(res.text)

        ws.send(json.dumps(
            {"cmd": "as",
             "params": {"cmd": "siteSetLimit", "address": tg_client.website.replace("/", ""), "params": "200"},
             "id": 1000001}))
        r = ws.recv()
        logger.debug(r)

        res = requests.get(tg_client.server_url + "content.json", headers={"ACCEPT": "text/html"})
        # logger.debug(res.text)
        res = requests.get(tg_client.zeronet_url + "/raw" + tg_client.website + "attscript.html",
                           headers={"ACCEPT": "text/plain"})
        # logger.debug(res.text)

        dDialog.update(0, 'Controllo Aggiornamento Scripts')

        if name:
            name = unquoter(name)
            name = r'.*?(' + name.replace(" ", r"\s+").lower() + r').*?'
            rtype = re.MULTILINE
        else:
            name = r"(?:\s+|)(.*?)(?:\s+|)"
            rtype = re.S

        regex = r'<a href=\"(http[^\"]+)\">' + name + r'</a>'
        scripters = re.compile(regex, rtype | re.IGNORECASE).findall(res.text)

        tot = len(scripters)

        i = 1
        for url, scripter in scripters:
            scripter = scripter.replace("&nbsp;", "").replace("\n", "")
            url = url.replace("http://127.0.0.1:43110", tg_client.zeronet_url)
            if not url.endswith("/"):
                url += "/"
            # logger.debug(scripter + ": " + url + "content.json")
            requests.get(url, headers={"ACCEPT": "text/html"})
            ws_url = url.replace(tg_client.zeronet_url, "").replace("/", "")
            logger.debug(ws_url)

            ws.send(json.dumps(
                {"cmd": "as",
                 "params": {"cmd": "siteSetLimit", "address": ws_url, "params": "200"},
                 "id": 1000001}))
            r = ws.recv()

            requests.get(url + "content.json", headers={"ACCEPT": "text/html"})
            # logger.debug(res.text)

            ws.send(json.dumps({"cmd": "as", "params": {"cmd": "siteUpdate", "address": ws_url}, "id": 1000001}))
            r = ws.recv()
            logger.debug(r)

            dDialog.update((100 * i / tot), 'Ricevendo: ' + scripter)
            i += 1
            xbmc.sleep(250)

        ws.close()
    # logger.debug(res.text)
    except Exception as e:
        if kodiutils.get_setting_as_bool("debug"):
            import traceback
            traceback.print_stack()
            logger.debug(e)

    try:
        dDialog.close()
    except Exception as e:
        if kodiutils.get_setting_as_bool("debug"):
            import traceback
            traceback.print_stack()
            logger.debug(e)
        pass


def check_update():
    pDialog.create('Thegroove 360', 'Controllo Aggiornamenti')
    try:
        try:
            rv = get_remote_version()
        except Exception as e:
            import traceback
            traceback.print_stack()
            logger.debug(e)
            pDialog.close()
            return

        try:
            lv = get_local_version()
        except:
            return
        pDialog.update(100, message='Completato')
        if rv and rv != lv:
            pDialog.close()
            dDialog.create(xbmcaddon.Addon().getAddonInfo('id'), "Aggiornamento In Corso")
            download_new_release(rv)
        else:
            pDialog.close()
            epg_logos_update()
            resolver_update(force=False)

    except:
        raise
    finally:
        try:
            pDialog.close()
            dDialog.close()
        except Exception as e:
            if kodiutils.get_setting_as_bool("debug"):
                import traceback
                traceback.print_stack()
                logger.debug(e)
            pass


def epg_logos_update():
    try:
        import threading
        if kodiutils.get_setting_as_bool("show_epg"):
            epg = EpgLight(True)
            th_epg = threading.Thread(target=epg.get_epg_file, name="epg_updater")
            th_epg.daemon = True
            th_epg.start()
            # th_epg.join()

        if kodiutils.get_setting_as_bool("show_logos"):
            epg = EpgLight(True)
            th_logo = threading.Thread(target=epg.set_logos(), name="logos_updater")
            th_logo.daemon = True
            th_logo.start()
            # th_logo.join()
    except:
        raise


def download_new_release(ver):
    global tg_client
    tag_name = xbmcaddon.Addon().getAddonInfo('id') + "-" + ver + ".zip"
    res = requests.get(tg_client.server_url + "zipaddon/" + tag_name)
    out_name = "plugin.video.thegroove360"
    zip_temp = u'special://temp/%s.zip' % out_name
    xbmcvfs.delete(zip_temp)
    if sys.version_info[0] < 3:
        out_temp = xbmc.translatePath(zip_temp)
    else:
        out_temp = xbmcvfs.translatePath(zip_temp)
    total_length = res.headers.get('content-length', 0)
    if int(total_length) == 0:
        total_length = -1

    with open(out_temp, 'wb') as f:
        dl = 0
        total_length = float(float(total_length) / 1024)
        for data in res.iter_content(chunk_size=1024):
            dl += (len(data) / 1024)
            f.write(data)
            perc = int(dl * 100 / total_length)

            dDialog.update(perc, "Download " + str(dl) + "Kb di " + str(total_length) + "Kb")
        f.close()

    dDialog.update(0, "Aggiornamento Addon Alla versione " + tag_name)
    if sys.version_info[0] > 2:
        target_folder = xbmcvfs.translatePath(u'special://temp/')
    else:
        target_folder = xbmc.translatePath(u'special://temp/')

    try:
        install_zip(out_temp, target_folder, dDialog, tag_name)
        # version_file = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'thegroove_version.json')
        # with open(version_file, 'w') as latest_commit:
        #     del commit["committer_email"]
        #     del commit["author_email"]
        #     json.dump(commit, latest_commit)
        #     latest_commit.close()
    except:
        raise


def install_zip(zipped_file, unpack_folder, dialog, tag_name):
    dest_dir = xbmcaddon.Addon().getAddonInfo('path')
    global tg_client
    # logger.debug(zipped_file)

    try:
        with zipfile.ZipFile(zipped_file, 'r') as zfile:
            tot = len(zfile.infolist())
            zfile.extractall(path=unpack_folder)
            zfile.close()
    except zipfile.BadZipfile:
        import io
        from urllib2 import Request, urlopen
        try:
            req = Request(tg_client.server_url + "zipaddon/" + tag_name)
            content = urlopen(req).read()
            z = zipfile.ZipFile(io.BytesIO(content))
            z.extractall(path=unpack_folder)
            tot = len(z.infolist())
            z.close()
        except:
            raise
            # req = Request("http://127.0.0.1:43110/list/1Atp8zSnAXBKXGroQU8MeWvDdWcnyShW8B/zipaddon/" + tag_name)
            # content = urlopen(req).read()
            # raise

    os.remove(zipped_file)
    try:
        tmp_dir = glob(os.path.join(unpack_folder, 'plugin.video.thegroove360*'))[0]
    except:
        tmp_dir = None
        pass
    count = 0

    dev_folder = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), '.git')

    if os.path.exists(dev_folder):
        if tmp_dir:
            shutil.rmtree(tmp_dir)
        return

    for root, dirs, files in os.walk(tmp_dir):
        dst_dir = root.replace(tmp_dir, dest_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            perc = count * 100 / tot
            dialog.update(perc, "Aggiornamento Addon Alla versione " + tag_name)
            src_file = os.path.join(root, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                try:
                    if os.path.samefile(src_file, dst_file):
                        continue
                except AttributeError:
                    if os.stat(src_file) == os.stat(dst_file):
                        continue
                os.remove(dst_file)
            shutil.move(src_file, dst_dir)
            count += 1
    shutil.rmtree(tmp_dir)


def resolver_update(force=False):
    version_file = os.path.join(xbmcaddon.Addon('script.module.tg360resolver').getAddonInfo('path'), 'domains_version.json')
    vhash = ""
    if force:
        try:
            file_to_rem = pathlib.Path(version_file)
            file_to_rem.unlink()
        except Exception as E:
            print(E)
            import traceback
            traceback.print_stack()
            pass

    if os.path.exists(version_file):
        f = open(version_file, "r")
        data = json.loads(f.read())
        vhash = data["hash"]

    cli = HttpClient()
    r = cli.get_request("https://thegroove360.tk/scripters/Resolver/update/version.json")
    if r.status_code == 200:
        with open(version_file, 'w+') as outfile:
            outfile.write(r.text)
            outfile.close()

    res = cli.get_request("https://thegroove360.tk/scripters/Resolver/update/update.php?hash=" + vhash)
    logger.debug(res.status_code)
    logger.debug(res.text)

    if res.status_code == 200:
        import threading
        import resolver_360
        try:
            th_domains = threading.Thread(target=resolver_360.update_domains, name="domains_updater", args=(res.json(),))
            th_domains.daemon = True
            th_domains.start()
        except Exception as E:
            import traceback
            traceback.print_stack()
            print(E)
