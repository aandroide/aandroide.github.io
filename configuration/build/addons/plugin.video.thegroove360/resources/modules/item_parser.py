import logging
import xbmcaddon
import re

from resources.lib import kodilogging
from resources.modules.thegroove.thegroove_item import ThegrooveItem
from resources.modules.thegroove.thegroove_regexes import ThegrooveRegexes
from resources.modules.httpclient import HttpClient
from resources.lib import kodiutils

import resources.modules.thegroove.tmdb_wrapper as tmdbapi

try:
    import queue as mQueue
except ImportError:
    import Queue as mQueue

from resources.modules.thegroove import support

ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()


class ItemParser:

    def __init__(self):
        self.page_list = mQueue.Queue()
        self.regex_mode = None
        self.repeat_mode = None

    def parse_page(self, xml):
        try:
            logger.debug("______ parse page ______")
            regex = r'(<item>(?:.*?)</item>|<dir>(?:.*?)</dir>|<plugin>(?:.*?)</plugin>)'
            matches = re.compile(regex, re.MULTILINE | re.S).findall(xml)
            # queue = mQueue.Queue()
            for match in matches:
                self.page_list.put(match)

            self.parse_item_mt(self.page_list, use_lock=True)

        except Exception as e:
            raise e

    def parse_item(self, xml_item, parent_xml="", regexes=None):
        logger.debug("____________ PARSE ITEM ______________")

        # logger.debug(xml_item)

        li = ThegrooveItem()
        if regexes:
            # li.regexes.append(regexes)
            for rex in regexes:
                if type(rex) == dict:
                    rex = ThegrooveRegexes.dict_to_obj(rex)
                li.regexes.append(rex)

        li.parent_xml = parent_xml
        li._raw = xml_item

        xml_stripped = re.sub(r"<regex>(.*?)</regex>", "", xml_item, 0, re.MULTILINE | re.DOTALL)

        meta = re.compile(r'<meta>(.*?)</meta>', re.S).findall(xml_stripped)

        xml_stripped = re.sub(r"<meta>(.*?)</meta>", "", xml_stripped, 0, re.S)

        matches = re.compile(r'<([^/>]+)>', re.MULTILINE).findall(xml_stripped)

        # logger.debug(matches)

        for tag in matches:
            closure = tag.split(" ")[0]
            regex = '<' + tag + '>(.*?)</' + closure + '>'
            try:
                value = re.compile(regex, re.S).findall(xml_stripped)[0]
            except:
                value = ""

            # logger.debug(value)
            if tag == "name" or tag == "title":
                li.label = value  # u''.join(value).encode("utf-8").strip()

            if tag.startswith("link"):
                from resources.modules.thegroove.thegroove_httpclient import ThegrooveHttpClient as TGClient
                tg_cli = TGClient()
                if value.strip().startswith("/thegroove/") or value.strip().startswith(tg_cli.server_url):
                    is_thegroove_link = True
                else:
                    is_thegroove_link = False

                if is_thegroove_link or value.strip().startswith("$doregex["):
                    li.url = value

                    rxml = li.parent_xml if li.parent_xml != "" else li._raw
                    is_repeat_regex = ItemParser.is_repeat_regex(value, rxml)

                    if is_thegroove_link or is_repeat_regex:
                        li.is_folder = True
                    else:
                        li.is_folder = False
                        li.is_playable = True

                elif "<sublink" in value:
                    subls = re.compile(r'(<sublink(.*?)>(.*?)</sublink>)', re.MULTILINE).findall(value)
                    resolver_type = ""
                    for subxml, subpar, subl in subls:
                        name = ""
                        if subpar:
                            try:
                                name = re.compile(r'name=\"([^\"]+)\"', re.MULTILINE | re.DOTALL).findall(subpar)[0]
                            except:
                                name = ""
                            resolver_type = ThegrooveItem.get_thegroove_resolver(subxml, subl)
                        li.sublinks.append((name, subl, resolver_type))
                    li.is_folder = False
                    li.url = ""
                else:
                    # logger.debug("EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE")
                    li.tg_resolver = ThegrooveItem.get_thegroove_resolver(tag, value)
                    # logger.debug(li.tg_resolver)
                    try:
                        is_url = (value.index("://") or (value.startswith("plugin") or value.startswith(
                            "http")) or li.tg_resolver != "") >= 0
                        if is_url:
                            li.is_folder = False

                            if value.startswith("http"):
                                if li.tg_resolver == "extsrc":
                                    li.is_folder = True

                            li.url = value.strip()
                    except:
                        if li.tg_resolver == "" or not li.tg_resolver:
                            li.is_folder = True
                        else:
                            li.url = value.strip()
                            li.is_folder = False

            if tag == "thumbnail":
                li.arts["thumb"] = value

            if tag == "fanart":
                li.arts["fanart"] = value

            if tag == "plot":
                li.info["plot"] = value  # u''.join(value).encode("utf-8").strip().decode("utf-8", "ignore")

        if xml_item.startswith("<plugin>"):
            li.is_folder = False
            li.is_plugin = True

        if meta:
            try:
                if "makelist" not in meta and kodiutils.get_setting_as_bool("is_tmdb"):
                    li = tmdbapi.tmdb(meta[0], li)
            except:
                pass

        from resources.lib import plugin
        plugin.show_item(li)
        # self.page_list.append(li)

    def parse_regex(self, item):
        logger.debug("_________ PARSE REGEX ___________")
        # regex_name = re.compile(r'<link>\$doregex\[(.*?)\]</link>', re.MULTILINE).findall(xml_item)[0]
        regex_name = re.compile(r'\$doregex\[(.*?)\]', re.MULTILINE).findall(item.url)[0]

        # logger.debug(regex_name)
        # logger.debug(item.params)

        xml_item = item._raw if item.parent_xml == "" else item.parent_xml

        # logger.debug(xml_item)

        regex = r'<regex>(\s+<name>' + regex_name + '</name>.*?)</regex>'
        regex_tag = re.compile(regex, re.DOTALL).findall(xml_item)[0]

        # logger.debug(regex_tag)

        try:
            listrepeat = re.compile(r'<listrepeat>(.*?)</listrepeat>', re.DOTALL).findall(regex_tag)[0]
            # logger.debug(listrepeat)
        except:
            listrepeat = ""
        try:
            expres = re.compile(r'<expres>(.*?)</expres>', re.DOTALL).findall(regex_tag)[0]
            # logger.debug(expres)
        except:
            expres = ""
        try:
            page = re.compile(r'<page>(.*?)</page>', re.DOTALL).findall(regex_tag)[0]
            # logger.debug(page)
        except:
            page = ""

        repeat_mode_check = re.search('<.*?>.*?</.*?>', listrepeat, re.DOTALL)
        if repeat_mode_check:
            self.repeat_mode = "repeat"
        else:
            self.repeat_mode = "single"

        regex_mode_check = re.search(r'#\$pyFunction', expres, re.DOTALL)

        if regex_mode_check:
            self.regex_mode = "python"
        else:
            self.regex_mode = "regex"

        regex_param = re.compile(r'\$doregex\[.*?\]\((.*?)\)', re.MULTILINE).findall(item.url)
        if regex_param:
            page = regex_param[0]

        if self.repeat_mode == "single" and self.regex_mode == "python":
            return ItemParser.parse_py_regex(expres, item, page)

        if self.repeat_mode == "repeat" and self.regex_mode == "python":
            self.build_item_py(listrepeat, expres, regex_name, page, xml_item, item)

        if self.repeat_mode == "repeat" and self.regex_mode == "regex":
            self.build_item_re(listrepeat, expres, regex_name, page, xml_item, item)

        return ""

    def build_item_re(self, schema, expres, regex_name, page, parent_xml, item):
        logger.debug("________________ BUILD ITEM RE ________________")
        page = page.replace("<![CDATA[", "").replace("]]>", "")
        page = support.get_zeronet_page(page)
        r = HttpClient().get_request(page)
        expres = expres.replace("<![CDATA[", "").replace("]]>", "")
        res = re.compile(expres, re.MULTILINE).findall(r.text)

        self.build_item(res, regex_name, schema, parent_xml, item)

    def build_item_py(self, schema, fn, regex_name, page, parent_xml, item):
        logger.debug("________________ BUILD ITEM PY ________________")
        page = page.replace("<![CDATA[", "").replace("]]>", "")
        res = ItemParser.parse_py_regex(fn, item, page)
        self.build_item(res, regex_name, schema, parent_xml, item)

    def build_item(self, res, regex_name, schema, parent_xml, item):
        logger.debug("________________ BUILD ITEM ________________")

        outschema = "<item>" + schema + "</item>"
        outschema = outschema.replace("<![CDATA[", "").replace("]]>", "")

        self.page_list = mQueue.Queue()

        extra = None
        if type(res) is dict:
            extra = res["extra"]
            res = res["list"]

        self.item_builder(res, outschema, item, regex_name, parent_xml)

        if extra:
            extra_schema = re.compile(r'<extra>(.*?)</extra>', re.DOTALL).findall(parent_xml)[0]
            outschema = "<item>" + extra_schema + "</item>"
            outschema = outschema.replace("<![CDATA[", "").replace("]]>", "")
            self.item_builder(extra, outschema, item, regex_name, parent_xml)

        self.parse_item_mt(self.page_list, show_progress=True)

    def item_builder(self, res, outschema, item, regex_name, parent_xml):
        logger.debug("________________ ITEM BUILDER ________________")
        for r in res:
            out = outschema
            regexes = []

            if len(item.regexes) > 0:
                for regexp in item.regexes:
                    if type(regexp) == dict:
                        regexp = ThegrooveRegexes.dict_to_obj(regexp)
                    # logger.debug(regexp.params)
                    if regexp.name == regex_name:
                        continue
                    for j, p in enumerate(regexp.params):
                        print(p);out = out.replace("[" + regexp.name + ".param" + str((j + 1)) + "]", p.strip())
                    regexes.append(ThegrooveRegexes(name=regexp.name, params=regexp.params))

            for i, rparam in enumerate(r):
                # logger.debug(rparam)
                to_replace = "[" + regex_name + ".param" + str((i + 1)) + "]"
                if to_replace in out:
                    rp = u''.join(rparam).encode("utf-8").strip()
                    out = out.replace(to_replace, rp.decode('utf-8', 'ignore'))
            regexes.append(ThegrooveRegexes(name=regex_name, params=r))

            # logger.debug(out)
            self.page_list.put((out, parent_xml, regexes))

    def parse_item_mt(self, queue, use_lock=True, show_progress=False):
        from resources.modules.mt_worker import MTWorker
        MTWorker.set_jobs(queue, self.parse_item, use_lock=use_lock, show_progress=show_progress)

    @staticmethod
    def is_repeat_regex(name, xml):
        logger.debug("________________ IS REPEAT REGEX ________________")
        try:
            name = re.compile(r'\$doregex\[(.*?)\]').findall(name)[0]
        except IndexError:
            return False

        reg = r'<regex>.*?(<name>' + name + '</name>.*?)</regex>'
        matches = re.compile(reg, re.S).findall(xml)

        if len(matches) > 0:
            r = matches[0]
            lrms = re.compile(r'<listrepeat>(.*?)</listrepeat>', re.DOTALL).findall(r)
            if len(lrms) > 0:
                lrm = lrms[0]
                lrm = lrm.replace("<![CDATA[", "").replace("]]>", "")
                if lrm != "":
                    return True

        return False

    @staticmethod
    def replacer(fn, item):
        logger.debug("_____________REPLACER_________________")
        repl = re.compile(r'(\[(.*?)\.param(\d+)\])').findall(fn)

        functions = fn

        for rex in repl:
            rr = rex[0]
            rname = rex[1]
            rpar = rex[2]
            for p in item.regexes:
                # logger.debug(p)
                if p["name"] == rname:
                    opar = ""
                    if p["name"] == rname:
                        try:
                            opar = p["params"][(int(rpar) - 1)]
                        except IndexError:
                            opar = ""
                    functions = functions.replace(rr, opar)

        # logger.debug(functions)

        return functions

    @staticmethod
    def parse_py_regex(fn, item, page):
        logger.debug("________________ PARSE PY REGEX ________________")
        try:
            # logger.debug(fn)
            functions = re.compile(r'<!\[CDATA\[#\$pyFunction(.*?)]]>', re.DOTALL).findall(fn)[0]
        except:
            raise

        functions = ItemParser.replacer(functions, item)
        # logger.debug(functions)
        page = support.get_zeronet_page(page)

        xml_py_res = ""
        if functions != "":
            functions += "\nxml_py_res = get_thegroove_xml_fn('" + page + "')"
            try:
                loc = {}
                exec(functions, globals(), loc)
                # logger.debug(loc)
                xml_py_res = loc["xml_py_res"]
            except Exception as e:
                if kodiutils.get_setting_as_bool("debug"):
                    import traceback
                    traceback.print_stack()
                    logger.debug(str(e))
                raise e

        # logger.debug(type(xml_py_res))
        # logger.debug(xml_py_res)

        return xml_py_res