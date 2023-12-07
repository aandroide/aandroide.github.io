import re

from conf.common import CommonResolver


class Maxstream(CommonResolver):

    def set_request_headers(self):
        self.request_headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 9; SM-G950F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36"}

    def find_stream(self):
        return [r"sources:\s.*?src:\s\"([^\"]+)\""]

    def set_referer(self, url):
        ref = self.resolver.stack[-1]
        ref_host = re.compile(r'(http.*?//.*?/)', re.MULTILINE).findall(ref)[0]
        return "!Referer=" + ref_host + "&Origin=" + ref_host[:-1]
