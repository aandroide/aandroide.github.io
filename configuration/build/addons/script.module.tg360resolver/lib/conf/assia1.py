import re

from conf.common import CommonResolver


class Assia1(CommonResolver):

    def set_referer(self, url):
        ref = self.resolver.stack[-1]
        ref_host = re.compile(r'(http.*?//.*?/)', re.MULTILINE).findall(ref)[0]
        ua = self.resolver.cli.get_random_ua()
        return "!Referer=" + ref_host + "&Origin=" + ref_host[:-1] + "&user-agent=" + ua
