import re

from conf.common import CommonResolver


class DaddyLive(CommonResolver):

    def find_page_src(self, src):
        source = re.compile(r'(<article.*?</article>)', re.S).findall(src)[0]
        return source

    def set_referer(self, url):
        ref = self.resolver.stack[-1]
        ref_host = re.compile(r'(http.*?//.*?/)', re.MULTILINE).findall(ref)[0]
        return "!Referer=" + ref_host + "&Origin=" + ref_host[:-1]
