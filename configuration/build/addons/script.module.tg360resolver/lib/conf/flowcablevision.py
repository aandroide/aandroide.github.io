import re

from conf.common import CommonResolver


class FlowcableVision(CommonResolver):

    def find_stream(self):
        if "embed.php" not in self.page_url:
            return []

        stream_url = \
            re.compile(r"var\ssiteUrl.*?var stream_url\s=\s'([^']+)'", re.MULTILINE | re.DOTALL).findall(self.page_src)[
                0]

        import base64

        token = re.compile(r"source:\s.*?\+'([^']+)'", re.MULTILINE | re.DOTALL).findall(self.page_src)[0]

        ref = self.resolver.find_hostname(self.page_url)
        ua = self.resolver.cli.headers["user-agent"]
        url = base64.b64decode(stream_url).decode() + token + "|!Referer=" + ref + "&user-agent=" + ua

        return [url]
