import xbmcaddon
from httpclient import HttpClient
import logging
import re
from urllib.parse import quote as quoter
from urllib.parse import urlparse

from jsbeautifier.unpackers import packer
import conf
from conf import *

logger = logging.getLogger(xbmcaddon.Addon().getAddonInfo('id'))


class SportResolver:
    def __init__(self, url):
        self.start_url = url
        self.src = []
        self.cli = HttpClient()
        self.headers = {}
        self.resolved = False
        self.resolved_urls = []
        self.resolvers = []
        self.set_resolvers()
        self.stack = []

    def find_page_src(self, url=None, src=None):
        page_src = ""
        if url is None and src is None:
            url = self.start_url
        if src is not None:
            page_src = src
        elif url is not None:
            if ".m3u8" in url or url.endswith(".mpd"):
                return url
            try:
                h = self.cli.session.head(url, timeout=1)
                header = h.headers
                content_type = header.get('content-type')
                logger.debug("CONTENT TYPE: " + str(content_type))
                if content_type and "video" in content_type:
                    return url
            except:
                pass
            self.headers["referer"] = self.find_hostname(url) + "/"
            url, page_src = self.check_for_stream(url)
            if self.resolved:
                self.resolved_urls.append(self.compose_url(page_src))
                return url

        matches = self.find_iframe(page_src, url)

        if not matches:
            return None

        for match in matches:
            self.headers["referer"] = self.find_hostname(url)
            rurl, ret = self.check_for_stream(match)
            if self.resolved:
                checks = re.compile(r'^http.*?//.*?$', re.DOTALL).findall(ret)
                if checks:
                    self.resolved_urls.append(self.compose_url(ret))
                return

            self.find_page_src(url=rurl, src=ret)

    def find_iframe(self, page_src, url):
        logger.debug("______________ FIND IFRAMES ___________")
        matches = None
        for r in self.resolvers:
            obj = r["obj"]
            servs = obj.servers

            for ser in servs:
                if ser in url:
                    page_src = self.find_custom_page_src(obj, page_src)
                    matches = self.find_custom_page(obj, page_src)
                    break

        if not matches:
            matches = re.compile(r'<iframe.*?src=[\'|\"]([^\'|\"]+)[\'|\"].*?>',
                                 re.MULTILINE | re.IGNORECASE | re.S).findall(page_src)

        logger.debug("IFRAMES:")
        logger.debug(matches)

        return matches

    def check_for_stream(self, url):
        logger.debug("______________ CHECK FOR STREAM ___________")
        logger.debug(url)
        if url.startswith("//"):
            url = "http:" + url
        if url.startswith("/"):
            url = self.find_hostname(self.start_url) + url
        custom_headers = self.headers

        custom_server = None

        for r in self.resolvers:
            obj = r["obj"]
            servs = obj.servers
            for ser in servs:
                if ser in url:
                    custom_server = obj
                    custom_headers = {**self.headers, **obj.request_headers}
                    break

        if not custom_server:
            for r in self.resolvers:
                obj = r["obj"]
                servs = obj.servers
                for ser in servs:
                    if ser in self.start_url:
                        custom_server = obj
                        custom_headers = {**self.headers, **obj.request_headers}
                        break

        if custom_server and custom_server.use_last_domain:
            last = custom_server.servers[-1]
            if last not in url:
                url = re.sub(r"(http.*?://)(.*?/)", "\\1" + last + "/", url, 0, re.DOTALL)
        res = self.cli.get_request(url, headers=custom_headers)
        res_cont = res.text
        url = res.url

        res_cont += self.check_packed(res_cont)

        matches = None

        if custom_server:
            custom_server.set_page_url(url)
            matches = self.find_custom_stream_url(custom_server, res_cont)

        if not matches:
            matches = self.find_stream_url(res_cont)

        if matches:
            # match = matches[0]
            self.resolved = True
            self.stack.append(url)
            if len(matches) == 1 and matches[0] is not tuple:
                return url, matches[0]
            return url, matches
        else:
            return url, res_cont

    def find_custom_page_src(self, obj, page_src):
        new_src = obj.find_page_src(page_src)

        if new_src:
            return new_src
        return page_src

    def find_custom_page(self, obj, page_src):
        regexes = obj.find_page()
        matches = []

        if regexes:
            for regex in regexes:
                ms = re.compile(regex, re.MULTILINE | re.IGNORECASE).findall(page_src)
                for m in ms:
                    matches.append(m)

        return matches

    def find_custom_stream_url(self, obj, page_src):
        logger.debug("_______________ FIND CUSTOM STREAM URL ____________________________")
        obj.set_page_src(page_src)
        regexes = obj.find_stream()
        matches = []

        if regexes:
            for regex in regexes:
                if (isinstance(regex, str) and regex.startswith("http")) or isinstance(regex, tuple):
                    matches.append(regex)
                else:
                    ms = re.compile(regex, re.MULTILINE | re.IGNORECASE).findall(page_src)
                    for m in ms:
                        mp = obj.parse_stream(m)
                        if mp:
                            m = mp
                        matches.append(m)

        return matches

    def find_stream_url(self, page_src):
        logger.debug("_______________ FIND STREAM URL ____________________________")

        solver = re.compile(r'(janjuaplayer.com)').findall(page_src)
        matches = None
        if solver:
            from conf.janjuaplayer import JanjuaPlayer
            janjua = JanjuaPlayer(self, page_src)
            matches = [janjua.find_stream()]

        if not matches:
            matches = re.compile(r'source:.*?window.atob\([\'|\"]([^\'|\"]+)[\'|\"]\)',
                                 re.MULTILINE | re.IGNORECASE).findall(page_src)
            if matches:
                import base64
                matches[0] = base64.b64decode(matches[0]).decode('utf-8')
        logger.debug("first matches")
        logger.debug(matches)
        if not matches:
            matches = re.compile(r'[^/*]source:.*?[\'|\"]([^\'|\"]+)[\'|\"]',
                                 re.MULTILINE | re.IGNORECASE).findall(page_src)

            ms = []
            for match in matches:
                if "google" not in match:
                    ms.append(match)

            matches = ms

            logger.debug("second matches")
            logger.debug(matches)

        return matches

    def check_packed(self, page_src):
        unpaks = ""
        if packer.detect(page_src):
            packs = re.compile(
                r'(<script>eval[ ]*\([ ]*function[ ]*\([ ]*p[ ]*,[ ]*a[ ]*,[ ]*c[ ]*,[ ]*k[ ]*,[ ]*e[ ]*,[ ]*.*?</script>)',
                re.S).findall(page_src)

            for pack in packs:
                unpaks += packer.unpack(pack)

        # logger.debug("UNPACKED:")
        # logger.debug(unpaks)

        return unpaks

    def compose_url(self, url):
        url_headers = ""
        or_url = url
        if isinstance(url, dict):
            url = or_url[0][1]
        for r in self.resolvers:
            obj = r["obj"]
            servs = obj.servers

            for ser in servs:
                if ser in self.start_url:
                    url_headers = obj.set_referer(url)
                    break
                if ser in self.stack[-1]:
                    ref = self.stack[-1]
                    ref_host = re.compile(r'(http.*?//.*?/)', re.MULTILINE).findall(ref)[0]
                    url_headers = "!Referer=" + ref_host + "&Origin=" + ref_host[:-1]
                    break
        if not url_headers:
            url_headers = "!Referer=" + self.find_hostname(url)

        if isinstance(or_url, tuple):
            return or_url[1] + "|" + url_headers

        if isinstance(or_url, list):
            ret = []
            for u in or_url:
                if isinstance(u, tuple):
                    ret.append((u[0], u[1] + "|" + url_headers))
                else:
                    ret.append(u[0] + "|" + url_headers)
            return ret

        # if "Referer" not in url:
        #    return url + "|!Referer=%s" % hostname
        return url + "|" + url_headers

    @staticmethod
    def find_hostname(url):
        parsed = urlparse(url)

        netloc = parsed.netloc
        matches = re.compile(r'^.+\.([^.]+\.[^.]+)$', re.DOTALL).findall(parsed.netloc)
        if matches:
            netloc = matches[0]

        hostname = parsed.scheme + "://" + netloc

        logger.debug("HOST NAME:" + hostname)
        return hostname

    def set_resolvers(self):
        for cls in conf.common.CommonResolver.__subclasses__():
            self.resolvers.append({"name": cls.__name__, "obj": cls(self)})
