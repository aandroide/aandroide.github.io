import re

from conf.common import CommonResolver


class Bitporno(CommonResolver):

    def find_stream(self):
        matches = re.compile(r"file:\s\"([^\"]+)\"", re.DOTALL).findall(self.page_src)
        url = matches[0]

        return [self.resolver.find_hostname(self.page_url) + url]
