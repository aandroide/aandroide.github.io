from conf.common import CommonResolver
import re
import urllib
from urllib.parse import urlparse
from urllib.parse import parse_qs


class Eplayer(CommonResolver):

    def set_servers(self):
        return ['eplayer.click']

    def set_request_headers(self):
        self.request_headers = {"referer": self.resolver.start_url}

    def find_page_src(self, src):
        try:
            matches = re.compile(r">\s+str='([^\']+)'", re.MULTILINE).findall(src)[0]
            iframe_src = urllib.parse.unquote(matches.replace('@', "%"))
            url = re.compile(r'\.src=`([^`]+)`', re.MULTILINE).findall(iframe_src)[0]
            parsed_url = urlparse(self.page_url)
            stream_id = parse_qs(parsed_url.query)['id'][0]
            url = url.replace('${id}', stream_id)
            return "<iframe src='" + url + "'>"
        except:
            return src



