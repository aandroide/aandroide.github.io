import re

from conf.common import CommonResolver


class FindsportsStream(CommonResolver):

    def find_stream(self):
        # ref = self.resolver.stack[-1]
        atob = re.compile(r"atob\('([^']+)'\)", re.MULTILINE).findall(self.page_src)[0]
        import base64
        m3u8 = base64.b64decode(atob).decode()
        base = re.compile(r'(http.*?://.*?)/', re.MULTILINE).findall(self.page_url)[0]
        ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"
        url = base + m3u8 + "|!Referer=" + self.page_url + "&user-agent=" + ua

        return [url]
