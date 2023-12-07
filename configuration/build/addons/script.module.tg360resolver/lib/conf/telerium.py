import base64
import json
import re
import urllib.parse
from datetime import datetime, timedelta
from conf.common import CommonResolver


class Telerium(CommonResolver):

    def set_servers(self):
        return ['teleriumtv.com']

    def find_stream(self):
        headers = {
            'Referer': urllib.parse.unquote(self.page_url),
        }

        cookies = {'elVolumen': '100',
                   '__ga': '100'}

        tltv = base64.b64decode("aHR0cHM6Ly90ZWxlcml1bS50dg==").decode('utf-8')

        datenow = datetime.utcnow().replace(second=0, microsecond=0)
        datenow = datenow + timedelta(days=1)
        epoch = datetime(1970, 1, 1)
        timer = (datenow - epoch).total_seconds()
        datetoken = int(timer) * 1000
        chid = re.compile(r".*?/([\d]+)", re.DOTALL).findall(self.page_url)[0]
        json_url = tltv + "/streams/" + chid + "/" + str(datetoken) + ".json"
        # print("jsonUrl: " + jsonUrl)
        res = self.resolver.cli.get_request(json_url, headers=headers, cookies=cookies)
        # print("html: " + res.text)
        tokens = json.loads(res.text)
        cdn = tokens['url']
        next_url = tltv + tokens['tokenurl']
        # print("nexturl: " + nexturl)

        res = self.resolver.cli.get_request(next_url, headers=headers, cookies=cookies)

        tokens = json.loads(res.text)
        token_html = tokens[10][::-1]
        # print("tokenHtml: " + tokenHtml)

        # Parse the final URL
        stream = 'https:{0}{1}|!Referer={2}&!User-Agent={3}&Origin={4}&Sec-Fetch-Mode=cors'
        u = stream.format(cdn, token_html, urllib.parse.quote(self.page_url, safe=''),
                          self.resolver.cli.headers["user-agent"],
                          tltv)

        # print("url: " + u)
        return [u]
