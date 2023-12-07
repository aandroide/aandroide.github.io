import re

from conf.common import CommonResolver


class Liveon(CommonResolver):

    def find_page_src(self, src):
        fid = re.compile(r"fid='([^']+)';", re.MULTILINE).findall(self.page_src)[0]
        iframe = "https://vikistream.com/embed2.php?player=desktop&live=" + fid

        return "<iframe src='" + iframe + "'>"

    def find_stream(self):
        if self.page_url != self.resolver.start_url:
            link = re.compile(r'return\(\[(.*?)\].join', re.MULTILINE).findall(self.page_src)[0]
            link = link.split(",")
            link = ''.join(link)
            link = link.replace("\\", "").replace("\"", "")
            return [link]

    def set_referer(self, url):
        ref = self.resolver.stack[-1]
        ref_host = re.compile(r'(http.*?//.*?/)', re.MULTILINE).findall(ref)[0]
        return "!Referer=" + ref_host + "&Origin=" + ref_host[:-1]
