import requests
from datetime import date, datetime, timedelta
import os
import gzip
import glob
import sys

import xml.etree.ElementTree as ET

import sqlite3
from sqlite3 import Error

import difflib
import json
import re

try:
    import xbmcaddon
    import xbmc
    import xbmcgui
    import xbmcvfs
    from resources.lib import kodiutils
except ImportError:
    pass


class Epg:

    def __init__(self, progress=False, bg=True):
        self.epg_url = "http://www.epgitalia.tv/xml/guide.gzip"
        self.logos_url = "http://www.epgitalia.tv/wp-content/uploads/2019/06/Log-Tv-2019.zip"
        if sys.version_info[0] > 2:
            self.work_dir = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        else:
            self.work_dir = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        self.epg_db = "epg.sqlite"
        self.pDialog = None
        if progress and bg:
            self.pDialog = xbmcgui.DialogProgressBG()
        if progress and not bg:
            self.pDialog = xbmcgui.DialogProgress()
        self.epg_file = ""
        self.db_conn = None
        self.channel_names = []
        self.logo_names = []
        self.bg = bg

    def get_epg_file(self, force=False):
        today = date.today()
        d = today.strftime("%d_%m_%Y")

        epg_file = os.path.join(self.work_dir, "epg-" + d + ".xml")

        if os.path.exists(epg_file) and not force:
            self.epg_file = epg_file
            return epg_file
        else:
            try:
                for fl in glob.glob(os.path.join(self.work_dir, "epg-*.xml")):
                    os.remove(fl)

                for fl in glob.glob(os.path.join(self.work_dir, "ch_names-*.json")):
                    os.remove(fl)

                res = requests.get(self.epg_url)
                open(epg_file + ".gz", 'wb').write(res.content)

                p = open(epg_file, "wb")
                try:
                    with gzip.open(epg_file + ".gz", "rb") as f:
                        data = f.read()
                        p.write(data)
                        p.close()
                except IOError:
                    import io
                    from urllib2 import Request, urlopen
                    req = Request(self.epg_url)
                    content_raw = urlopen(req).read()
                    data = gzip.GzipFile(fileobj=io.BytesIO(content_raw)).read()
                    p.write(data)
                    p.close()

                os.remove(epg_file + ".gz")

                try:
                    self.epg_file = epg_file
                    self.check_epg_updates(True)
                except:
                    raise

                self.epg_file = epg_file
                self.set_channels_names()
                return epg_file
            except:
                raise

    def set_logos(self, force=False):
        if self.pDialog:
            self.pDialog.create(xbmcaddon.Addon().getAddonInfo('name'), 'Aggiornamento Loghi')
            # self.pDialog.update(0, message='')
        from zipfile import ZipFile, BadZipfile
        logos_file = os.path.join(self.work_dir, "logos.zip")
        logos_path = os.path.join(self.work_dir, "logos")
        if force:
            try:
                import shutil
                shutil.rmtree(logos_path, ignore_errors=True)
                os.remove(logos_file)
            except OSError:
                pass
        if not os.path.exists(logos_path):
            try:
                os.mkdir(logos_path)
                res = requests.get(self.logos_url)
                open(logos_file, 'wb').write(res.content)
                try:
                    with ZipFile(logos_file, 'r') as zipObj:
                        self.unzip_logos(zipObj, logos_path)

                    zipObj.close()
                except BadZipfile:
                    import io
                    from urllib2 import Request, urlopen
                    req = Request(self.logos_url)
                    content = urlopen(req).read()
                    zipObj = ZipFile(io.BytesIO(content))
                    self.unzip_logos(zipObj, logos_path)

                os.remove(logos_file)
            except:
                raise

        if self.pDialog:
            self.pDialog.close()

    def unzip_logos(self, zipObj, logos_path):
        for i, zip_info in enumerate(zipObj.infolist()):
            if zip_info.filename[-1] == '/':
                continue
            zip_info.filename = os.path.basename(zip_info.filename.lower())
            zipObj.extract(zip_info, logos_path)
            if self.pDialog:
                if self.bg:
                    self.pDialog.update(i, message='Download Loghi')
                else:
                    self.pDialog.update(i, 'Download Loghi')

    def parse_epg(self, insert=False):
        if self.pDialog:
            self.pDialog.create(xbmcaddon.Addon().getAddonInfo('name'), 'Aggiornamento EPG')
            # self.pDialog.update(0, message='Download EPG')

        xml = ET.parse(self.epg_file)
        root = xml.getroot()
        progs = root.findall("programme")

        keys = ["start", "stop", "channel"]
        subkeys = ["title", "category", "desc", "date", "icon", "country", "episode-num", "credits"]

        programmes = []

        today = datetime.today()

        try:
            shift = kodiutils.get_setting_as_float("epg_time_shift")
            today = today + timedelta(minutes=shift)
        except:
            pass

        limit = today + timedelta(days=1)
        import time
        for i, prog in enumerate(progs):
            programme = []
            start = prog.get("start").split("+")[0].strip()[:-6]
            start_date = datetime(*(time.strptime(start, '%Y%m%d')[:-6]))

            if start_date > limit:
                continue

            for k in keys:
                try:
                    # programme[k] = prog.get(k).lower()
                    if k == "start" or k == "stop":
                        programme.append(prog.get(k).split("+")[0].strip())
                        # programme[k] = programme[k].split("+")[0].strip()
                    else:
                        programme.append(prog.get(k).lower())
                except Exception as e:
                    # programme[k] = None
                    programme.append(None)

            for s in subkeys:
                try:
                    if s == "credits":
                        epg_credits = prog.find(s)
                        # print(len(epg_credits))
                        if not epg_credits:
                            programme.append(None)
                            programme.append(None)
                            continue

                        props = epg_credits.findall("actor")
                        cr = ""
                        for prop in props:
                            cr += prop.text + ","
                        if cr != "":
                            programme.append(cr.strip(","))
                        else:
                            programme.append(None)

                        props = prog.find(s).findall("director")

                        dr = ""
                        for prop in props:
                            dr += prop.text + ","
                        if dr != "":
                            programme.append(dr.strip(","))
                        else:
                            programme.append(None)

                    elif s == "icon":
                        # programme[s] = prog.find(s).get("src")
                        programme.append(prog.find(s).get("src"))
                    else:
                        # programme[s] = prog.find(s).text
                        props = prog.findall(s)
                        pr = ""
                        for prop in props:
                            pr += prop.text + ","
                        programme.append(pr.strip(","))
                except:
                    # programme[s] = None
                    programme.append(None)

            if self.pDialog:
                perc = int(i * 100 / len(progs))
                if self.bg:
                    self.pDialog.update(perc, message='Aggiornamento EPG')
                else:
                    self.pDialog.update(perc, 'Aggiornamento EPG')

            # print(programme)

            programmes.append(programme)

        if insert:
            self.insert_programmes(programmes)
            if self.pDialog:
                self.pDialog.close()

        return programmes

    def db_connect(self):
        conn = None
        try:
            conn = sqlite3.connect(os.path.join(self.work_dir, self.epg_db))
            conn.row_factory = lambda col, row: {co[0]: row[i] for i, co in enumerate(col.description)}
            # conn.set_trace_callback(print)

            table = """CREATE TABLE IF NOT EXISTS "epg" (
                            "id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                            "channel"	TEXT NOT NULL,
                            "start"	TEXT DEFAULT NULL,
                            "stop"	TEXT DEFAULT NULL,
                            "title"	TEXT DEFAULT NULL,
                            "category"	TEXT DEFAULT NULL,
                            "desc"	TEXT DEFAULT NULL,
                            "date"	TEXT DEFAULT NULL,
                            "icon"	TEXT DEFAULT NULL,
                            "country"	TEXT DEFAULT NULL,
                            "episode-num"	TEXT DEFAULT NULL,
                            "cast" TEXT DEFAULT NULL,
                            "director" TEXT DEFAULT NULL 
                        );"""

            c = conn.cursor()
            c.execute(table)

            self.db_conn = conn
            return conn
        except Error as e:
            print(e)

        return conn

    def insert_programmes(self, programmes):
        # if not self.db_conn:
        # print(programmes)
        self.db_connect()
        try:
            sql = ''' INSERT INTO epg (start, stop, channel, title, category, desc, date, icon, country,
                                        "episode-num", cast, director)
                        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''

            cur = self.db_conn.cursor()
            cur.executemany(sql, programmes)
            cur.close()
            self.db_conn.commit()
        except Error as e:
            import traceback
            print(e)
            traceback.print_stack()
        finally:
            self.db_conn.close()

    def truncate_epg(self):
        # if not self.db_conn:
        self.db_connect()
        try:
            cur = self.db_conn.cursor()
            cur.execute('''DELETE FROM epg WHERE id>0;''')
            cur.execute('''DELETE FROM sqlite_sequence WHERE name=\'epg\';''')
            cur.close()
            self.db_conn.commit()

            cur = self.db_conn.cursor()
            cur.execute('''VACUUM;''')
            cur.close()

        except Error as e:
            print(e)
        finally:
            self.db_conn.close()

    def find_current_playing(self, channel):
        d = datetime.now()
        try:
            shift = kodiutils.get_setting_as_float("epg_time_shift")
            d = d + timedelta(minutes=shift)
        except:
            pass

        d = d.strftime("%Y%m%d%H%M%S")

        channel = self.normalize_name(channel, False)
        rows = []
        if channel:
            self.db_connect()
            cur = self.db_conn.cursor()

            cur.execute('''SELECT * FROM epg WHERE channel=? AND start<=? AND stop>=?''', (channel, d, d))
            rows = cur.fetchall()
            cur.close()
            self.db_conn.close()

        try:
            return rows[0]
        except Exception as e:
            print(e)
            import traceback
            traceback.print_stack()
            return ""

    def set_channels_names(self):

        today = date.today()
        d = today.strftime("%d_%m_%Y")

        names_file = os.path.join(self.work_dir, "ch_names-" + d + ".json")

        if os.path.exists(names_file):
            with open(names_file) as json_file:
                self.channel_names = json.load(json_file)
                return

        self.db_connect()
        cur = self.db_conn.cursor()

        cur.execute('''SELECT DISTINCT channel FROM epg''')
        rows = cur.fetchall()
        cur.close()
        self.db_conn.close()

        for r in rows:
            val = r.get("channel")
            self.channel_names.append(val)

        with open(names_file, 'w') as outfile:
            json.dump(self.channel_names, outfile)

    def set_logo_names(self):
        names_file = os.path.join(self.work_dir, "logos", "logo_names.json")

        if os.path.exists(names_file):
            with open(names_file) as json_file:
                self.logo_names = json.load(json_file)
                return

        self.logo_names = os.listdir(os.path.join(self.work_dir, "logos"))
        with open(names_file, 'w') as outfile:
            json.dump(self.logo_names, outfile)

    def find_local_logo(self, channel):
        channel = self.normalize_name(channel, True)
        if channel:
            logos_path = os.path.join(self.work_dir, "logos")
            local_logo = os.path.join(logos_path, str(channel))
            if os.path.exists(local_logo):
                return local_logo
        else:
            return None

    def check_epg_updates(self, insert=False):
        try:
            self.truncate_epg()
            self.parse_epg(insert)
            self.set_channels_names()
        except:
            raise

    def normalize_name(self, name, is_logo=True):
        name = name.lower()
        cutoff = 0.65
        if not self.channel_names and not is_logo:
            self.set_channels_names()
            cutoff = 0.7

        if not self.logo_names and is_logo:
            self.set_logo_names()

        if is_logo:
            names_dict = self.logo_names
        else:
            names_dict = self.channel_names

        name = re.sub(r"\[.*?\]", "", name, 0, re.MULTILINE)
        # import re
        # name = re.sub(r"\[.*?\]", "", name, 0, re.MULTILINE)
        # replacer = ["it ", "it:", "it :", "it | ", "it|", "[it]", "full ", "fhd", "sd", "hd", "vip", "hd2", "h265",
        #             "1080"]
        #
        # if is_logo:
        #     replacer.append("+1")
        #
        # name = re.sub(r"it$", "", name, 0, re.MULTILINE)
        # for repl in replacer:
        #     if is_logo and repl == "hd":
        #         continue
        #     name = name.replace(repl, "").strip()

        # if not is_logo:
        names = difflib.get_close_matches(name, names_dict, cutoff=cutoff)
        # print(names)
        if names:
            return names[0]
        else:
            return None

        # return name.encode('ascii', errors='ignore').decode("utf-8")

    @staticmethod
    def format_info(info, sitem):

        ch_name = sitem.label
        # url = url
        # logo = info[2]
        title = Epg.stringify_info(info["title"])
        category = Epg.stringify_info(info["category"])
        desc = Epg.stringify_info(info["desc"])
        date = Epg.stringify_info(info["date"])
        icon = Epg.stringify_info(info["icon"])
        country = Epg.stringify_info(info["country"])
        epiosode = Epg.stringify_info(info["episode-num"])
        ch_icon = Epg().find_local_logo(ch_name)
        start = Epg.stringify_info(info["start"])
        stop = Epg.stringify_info(info["stop"])

        cast = Epg.stringify_info(info["cast"])
        director = Epg.stringify_info(info["director"])

        # if len(title) > 50:
        #     prog_title = " ".join(title[:50].split(" ")[:-1])
        # else:
        #     prog_title = title

        start_stop = ""
        if start != "" or stop != "":
            start = start[8:-4] + ":" + start[10:-2]
            stop = stop[8:-4] + ":" + stop[10:-2]
            start_stop = " [S: " + start + " - E: " + stop + "]"

        item_title = ch_name + "[CR][COLOR limegreen]" + title + "[/COLOR]" + start_stop

        if category != "":
            category = " - [" + category + "][CR]"

        if date != "":
            date = " (" + date + ")"

        plot = "[COLOR yellow]" + title + "[/COLOR]" + date + "[CR]" + category + desc

        n_serie = ""
        n_ep = ""
        if epiosode != "":
            sitem.info["mediatype"] = "episode"
            try:
                if "." in epiosode:
                    n_serie, n_ep = epiosode.split(".")
                else:
                    n_serie, n_ep = re.compile(r"S([\d]+)\sE([\d]+)", re.DOTALL).findall(epiosode)
            except:
                pass
        # elif cast != "":
        #     sitem.info["mediatype"] = "movie"
        # else:
        #     sitem.info["mediatype"] = "tvshow"

        sitem.label = item_title
        sitem.arts["fanart"] = icon
        sitem.arts["thumb"] = ch_icon

        sitem.info["cast"] = cast.split(",") if cast != "" else []
        sitem.info["director"] = director.split(",")
        sitem.info["plot"] = plot
        sitem.info["year"] = date
        sitem.info["country"] = country.split(",")

        if n_ep != "":
            sitem.info["episode"] = int(n_ep)
        if n_serie != "":
            sitem.info["season"] = int(n_serie)

        return sitem

    @staticmethod
    def stringify_info(info):
        try:
            if info:
                return info
            else:
                return ""
        except:
            return ""
