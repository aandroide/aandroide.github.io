import re

from conf.common import CommonResolver


class SportsOnline(CommonResolver):

    def set_referer(self, url):
        ref = self.resolver.stack[-1]
        ref_host = re.compile(r'(http.*?//.*?/)', re.MULTILINE).findall(ref)[0]
        return "!Referer=" + ref_host + "&Origin=" + ref_host[:-1]
