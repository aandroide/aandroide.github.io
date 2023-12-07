import json
import re
from conf.common import CommonResolver


class StreamCommunity(CommonResolver):
    def __init__(self, resolver):
        super().__init__(resolver)
        self.use_last_domain = True

    def find_stream(self):

        iframe_url = re.compile(r'<div id=\"app\" data-page=\".*?embedUrl.*?;(http.*?)&quot;', re.MULTILINE).findall(self.page_src)
        
        if iframe_url:
            self.page_url = iframe_url[0].replace('&amp;', '&')

        page_src = self.resolver.cli.get_request(self.page_url)
        matches = re.compile(r'src="([^"]+)"', re.DOTALL).findall(page_src.text)
        if matches:
            url = matches[0].replace('&amp;', '&')
            r = self.resolver.cli.get_request(url,
                                              headers={'referer': self.resolver.find_hostname(
                                                  self.resolver.start_url) + "/"})
            ms = re.compile(r"window.masterPlaylist = ({.*?params:.*?{.*?},.*?})", re.DOTALL) \
                .findall(r.text)
            if ms:
                masterplaylist = ms[0]
                mediaurl = re.compile(r"url: '([^']+)'", re.MULTILINE).findall(masterplaylist)[0]
                mediaurl += "?"
                ps = re.compile(r".*?'([^']+)':.*?'(.*?)'(?:,|$)", re.MULTILINE | re.DOTALL).findall(masterplaylist)
                for p in ps:
                    k, v = p
                    mediaurl += k + "=" + v + "&"
                mediaurl = mediaurl.rstrip("&")

                res = self.resolver.cli.get_request(mediaurl)
                links = re.compile(r"RESOLUTION=\d+x(\d+).*?\s(http.*?token=(?:[^&]+).*?)$", re.MULTILINE).\
                    findall(res.text)
                if not links:
                    return [mediaurl]
                ret = []
                for link in links:
                    ret.append(link)

                return ret

        return []

    def set_referer(self, url):
        ref = self.resolver.stack[0]
        return "!Referer=" + ref + "&user-agent=" + self.resolver.cli.headers["user-agent"]
