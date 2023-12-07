from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    from resolver_360 import SportResolver


class JanjuaPlayer:
    def __init__(self, resolver: 'SportResolver', src):
        self.resolver = resolver
        self.src = src

    def find_stream(self):
        try:
            channel = re.compile(r"channel='([^']+)',").findall(self.src)[0]
            bal = "https://www.tvportremote.com/loadbalancer?104379"
            upstream = "https://www.janjua.tv/hembedplayer/" + channel + "/1/640/480"
            ref = self.resolver.find_hostname(upstream)

            res = self.resolver.cli.get_request(bal, headers={"referer": ref})
            redirect = re.compile('redirect=(.*)').findall(res.text)[0]

            res = self.resolver.cli.get_request(upstream, headers={"referer": ref})

            pk = re.compile(r'enableVideo\(\"([^\"]+)\"').findall(res.text)[0]

            url = re.compile(r'ea \+ \"(.*?)\"').findall(res.text)[0]
            url = "https://" + redirect + url + pk

            return url

        except:
            pass