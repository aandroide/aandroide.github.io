import re

from conf.common import CommonResolver


class Ragnaru(CommonResolver):

    def find_stream(self):
        url = re.compile(r'return\(\[(.*?)\]', re.MULTILINE).findall(self.page_src)[0]
        url = url.replace('"', '').replace(",", '').replace("\\/", "/")

        return [url]
