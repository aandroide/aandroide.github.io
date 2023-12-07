import re
from conf.common import CommonResolver


class AnimeUnity(CommonResolver):

    def set_request_headers(self):
        ua = self.resolver.cli.get_random_ua()
        self.request_headers = {
            "user-agent": ua
        }

    def find_stream(self):
        matches = re.compile(r"embed_url=\"([^\"]+)\"", re.DOTALL).findall(self.page_src)

        if matches:
            url = matches[0].replace('&amp;', '&')
            r = self.resolver.cli.get_request(url,
                                              headers={'referer': self.resolver.find_hostname(
                                                  self.resolver.start_url) + "/"})

            ms = re.compile(r"window.masterPlaylist = ({.*?params:.*?{.*?},.*?})", re.DOTALL).findall(r.text)

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
                links = re.compile(r"RESOLUTION=\d+x(\d+).*?\s(http.*?token=(?:[^&]+).*?)$", re.MULTILINE). \
                    findall(res.text)
                if not links:
                    return [mediaurl]
                ret = []
                for link in links:
                    ret.append(link)

                return ret

    def set_referer(self, url):
        ref = self.resolver.stack[0]
        return "!Referer=" + ref + "&user-agent=" + self.resolver.cli.headers["user-agent"]
