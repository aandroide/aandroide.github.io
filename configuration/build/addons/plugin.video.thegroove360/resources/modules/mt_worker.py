import concurrent
import concurrent.futures
import logging
import multiprocessing

import xbmcaddon
import xbmcgui
import xbmcplugin
from threading import Thread, Lock
from resources.modules.thegroove import support
from resources.lib import kodiutils
import sys

logger = logging.getLogger(xbmcaddon.Addon().getAddonInfo('id'))

try:
    import queue as mQueue
except ImportError:
    import Queue as mQueue


class MTWorker(Thread):

    def __init__(self, queue, fn, qsize, lock=None, show_progress=False, pb_dialog=None, *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self.queue = queue
        self.fn = fn
        self.lock = lock
        self.show_progress = show_progress
        self.pb_dialog = pb_dialog
        self.qsize = qsize
        self.stopped = False

    def stop(self):
        self.stopped = True

    def run(self):
        while True:
            if self.stopped:
                break
            if self.lock:
                with self.lock:
                    self.run_thread()
            else:
                self.run_thread()

    def run_thread(self):
        logger.debug("__________________ RUN THREAD ________________")
        try:
            logger.debug(self.stopped)
            if not self.stopped:
                params = self.queue.get()
                if params is None:
                    self.stop()
                    return self.queue.task_done()
                if type(params) == tuple:
                    self.fn(*params)
                else:
                    self.fn(params)
        except Exception as E:
            import traceback
            traceback.print_stack()
            logger.debug(E)
            raise
        finally:
            if self.show_progress:
                if self.pb_dialog.iscanceled():
                    self.queue.task_done()
                    self.stop()
                    from resources.lib.plugin import plugin
                    xbmcplugin.endOfDirectory(plugin.handle)
                    self.pb_dialog.close()
                    self.queue.task_done()
                    return

                # logger.debug(self.queue.unfinished_tasks)
                item_counter = self.qsize - self.queue.unfinished_tasks
                percent = int((item_counter * 100) / self.qsize)
                self.pb_dialog.update(percent, "Elaborando Elementi %s di %s" % (item_counter, self.qsize))
            if not self.stopped:
                self.queue.task_done()

    @staticmethod
    def set_jobs(queue, fn, use_lock=False, show_progress=False):
        logger.debug("_____________ SET JOBS ____________________")

        # logger.debug(show_progress)
        pb_dialog = xbmcgui.DialogProgress()
        if show_progress:
            addon_name = xbmcaddon.Addon().getAddonInfo('name')
            pb_dialog.create(addon_name, "Loading items")

        if queue.qsize() > 1000:
            use_lock = False

        mt_list = ['Auto', 1, 2, 4, 8, 16]
        nthreads = support.get_cores_num()
        max_threads = kodiutils.get_setting_as_int("max_threads")
        # logger.debug("MAX THREADS " + str(max_threads))
        if max_threads != 0:
            nthreads = min(mt_list[max_threads], nthreads)
        logger.debug("NCORES " + str(nthreads))

        if sys.version_info[0] > 3:
            with concurrent.futures.ThreadPoolExecutor(max_workers=nthreads) as executor:
                futures = []
                items_list = []

                sentinel = object()
                i = 0
                for params in iter(queue.get, sentinel):
                    logger.debug(params)

                    if type(params) == tuple:
                        params["pos"] = i

                    # if pb_dialog.iscanceled():
                    #    break

                    logger.debug(params)
                    futures.append(executor.submit(fn, *params))
                    i += 1

                for future in concurrent.futures.as_completed(futures):
                    items_list.append(future.result())
                    logger.debug(items_list)

                try:
                    sorted_list = sorted(items_list, key=lambda it: int(it.getProperty("pos")))
                except:
                    sorted_list = items_list

                for li in sorted_list:
                    from resources.lib import plugin
                    plugin.show_item(li)


        else:
            if use_lock:
                lock = Lock()
            else:
                lock = None

            qsize = queue.qsize()
            threads = []
            for x in range(nthreads):
                worker = MTWorker(queue, fn, qsize, lock=lock, show_progress=show_progress, pb_dialog=pb_dialog)
                worker.daemon = True
                worker.start()
                threads.append(worker)

            queue.join()

            for i in range(nthreads):
                queue.put(None)

            for t in threads:
                t.stop()
                t.join()

        if show_progress:
            pb_dialog.close()
