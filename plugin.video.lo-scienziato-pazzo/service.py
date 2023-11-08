# -*- coding: utf-8 -*-
import datetime
import math
import os
import sys
import threading
import traceback
import xbmc

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit
# on kodi 18 its xbmc.translatePath, on 19 xbmcvfs.translatePath
try:
    import xbmcvfs
    xbmc.translatePath = xbmcvfs.translatePath
except:
    pass
from platformcode import config
librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)
os.environ['TMPDIR'] = config.get_temp_file('')

from core import httptools, scrapertools, db
from lib import schedule
from platformcode import logger, platformtools, updater, xbmc_videolibrary
from servers import torrent

# if this service need to be reloaded because an update changed it
needsReload = False
# list of threads
threads = []






def updaterCheck():
    global needsReload
    # updater check
    updated, needsReload = updater.check(background=True)


def get_ua_list():
    # https://github.com/alfa-addon/addon/blob/master/plugin.video.alfa/platformcode/updater.py#L273
    logger.info()
    url = "http://omahaproxy.appspot.com/all?csv=1"

    try:
        current_ver = config.get_setting("chrome_ua_version", default="").split(".")
        data = httptools.downloadpage(url, alfa_s=True).data
        new_ua_ver = scrapertools.find_single_match(data, "win64,stable,([^,]+),")

        if not current_ver:
            config.set_setting("chrome_ua_version", new_ua_ver)
        else:
            for pos, val in enumerate(new_ua_ver.split('.')):
                if int(val) > int(current_ver[pos]):
                    config.set_setting("chrome_ua_version", new_ua_ver)
                    break
    except:
        logger.error(traceback.format_exc())


def run_threaded(job_func, args):
    job_thread = threading.Thread(target=job_func, args=args)
    job_thread.start()
    threads.append(job_thread)


def join_threads():
    logger.debug(threads)
    for th in threads:
        try:
            th.join()
        except:
            logger.error(traceback.format_exc())


class AddonMonitor(xbmc.Monitor):
    def __init__(self):
        self.settings_pre = config.get_all_settings_addon()

        self.updaterPeriod = None
        self.update_setting = None
        self.update_hour = None
        self.scheduleScreenOnJobs()
        self.scheduleUpdater()
        self.scheduleUA()

        if not needsReload:  # do not run videolibrary update if service needs to be reloaded
            # videolibrary wait
            update_wait = [0, 10000, 20000, 30000, 60000]
            wait = update_wait[int(config.get_setting("update_wait", "videolibrary"))]
            if wait > 0:
                xbmc.sleep(wait)
            self.scheduleVideolibrary()
        super(AddonMonitor, self).__init__()


    def onNotification(self, sender, method, data):
        # logger.debug('METHOD', method, sender, data)
        if method == 'Playlist.OnAdd':
            from core import db
            db['OnPlay']['addon'] = True
            db.close()
        elif method == 'Player.OnStop':
            from core import db
            db['OnPlay']['addon'] = False
            db.close()
        elif method == 'VideoLibrary.OnUpdate':
            xbmc_videolibrary.set_watched_on_kod(data)
            logger.debug('AGGIORNO')

    def onScreensaverActivated(self):
        logger.debug('screensaver activated, un-scheduling screen-on jobs')
        schedule.clear('screenOn')

    def onScreensaverDeactivated(self):
        logger.debug('screensaver deactivated, re-scheduling screen-on jobs')
        self.scheduleScreenOnJobs()

    def scheduleUpdater(self):
        if not config.dev_mode():
            updaterCheck()
            self.updaterPeriod = config.get_setting('addon_update_timer')
            schedule.every(self.updaterPeriod).hours.do(updaterCheck).tag('updater')
            logger.debug('scheduled updater every ' + str(self.updaterPeriod) + ' hours')

    def scheduleUA(self):
        get_ua_list()
        schedule.every(1).day.do(get_ua_list)

    def scheduleVideolibrary(self):
        self.update_setting = config.get_setting("update", "videolibrary")
        # 2 = Daily, 3 = When Kodi starts and daily, 5 = Each time you start Kodi and daily
        if self.update_setting in [2, 3, 5]:
            self.update_hour = config.get_setting("everyday_delay", "videolibrary") * 4
            schedule.every().day.at(str(self.update_hour).zfill(2) + ':00').do(run_threaded, check_for_update, (False,)).tag('videolibrary')
            logger.debug('scheduled videolibrary at ' + str(self.update_hour).zfill(2) + ':00')

    def scheduleScreenOnJobs(self):
        schedule.every().second.do(platformtools.viewmodeMonitor).tag('screenOn')
        schedule.every().second.do(torrent.elementum_monitor).tag('screenOn')

    def onDPMSActivated(self):
        logger.debug('DPMS activated, un-scheduling screen-on jobs')
        schedule.clear('screenOn')

    def onDPMSDeactivated(self):
        logger.debug('DPMS deactivated, re-scheduling screen-on jobs')
        self.scheduleScreenOnJobs()


if __name__ == "__main__":
    logger.info('Starting KoD service')

    # Test if all the required directories are created
    config.verify_directories_created()

    if config.get_setting('autostart'):
        xbmc.executebuiltin('RunAddon(plugin.video.' + config.PLUGIN_NAME + ')')

    # check if the user has any connection problems
    from platformcode.checkhost import test_conn
    run_threaded(test_conn, (True, not config.get_setting('resolver_dns'), True, [], [], True))

    monitor = AddonMonitor()

    # mark as stopped all downloads (if we are here, probably kodi just started)
    from specials.downloads import stop_all
    try:
        stop_all()
    except:
        logger.error(traceback.format_exc())

    while True:
        try:
            schedule.run_pending()
        except:
            logger.error(traceback.format_exc())

        if needsReload:
            join_threads()
            db.close()
            logger.info('Relaunching service.py')
            xbmc.executeJSONRPC(
                '{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "plugin.video.kod", "enabled": false }}')
            xbmc.executeJSONRPC(
                '{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "plugin.video.kod", "enabled": true }}')
            logger.debug(threading.enumerate())
            break

        if monitor.waitForAbort(1): # every second
            logger.debug('KoD service EXIT')
            # db need to be closed when not used, it will cause freezes
            join_threads()
            logger.debug('Close Threads')
            db.close()
            logger.debug('Close DB')
            break
    logger.debug('KoD service STOPPED')