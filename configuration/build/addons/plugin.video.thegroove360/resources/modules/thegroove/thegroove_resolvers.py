import xbmcaddon
import logging
import sys

from resources.lib import kodiutils
from resources.modules.httpclient import HttpClient

resolvers = {
    "f4m": "plugin://plugin.video.f4mTester/?url={0}&streamtype=TSDOWNLOADER&name={1}",
    "ace": "plugin://program.plexus/?url={0}&mode=1&name={1}" if kodiutils.get_setting_as_bool("use_plexus") else "{0}",
    "sop": "plugin://program.plexus/?url={0}&mode=2&name={1}",
    "resolve": "{0}",
    "youtube": "plugin://plugin.video.youtube/play/?video_id={0}",  # id del video
    "sportsdevil": "plugin://plugin.video.SportsDevil/?mode=1&item=catcher%3dstreams%26url={0}%26videoTitle={1}",
    "tor": "plugin://plugin.video.elementum/play?uri={0}",
    "extsrc": "{0}",
    "tltv": "{0}",
    "dbstr": "{0}",
    "m3u": "{0}",
}

logger = logging.getLogger(xbmcaddon.Addon().getAddonInfo('id'))

vod_ext = ("mp4", "avi", "mkv", "mpeg", "flv", "3gp")


def ace_hash(play_url):
    if "acestream" in play_url:
        play_url = play_url.replace("acestream://", "")

    return play_url.strip()


def f4m(play_label, play_url):
    # if sys.version_info[0] > 2:
    #    return play_label, play_url
    if ".m3u8" not in play_url:
        return play_label, play_url

    play_label = play_label.replace("|", " ")
    play_url = play_url.replace("&amp;", "&")

    try:
        play_label = play_label.split("[CR]")[0]
    except:
        pass
    try:
        play_url_cut = play_url.split("?")[0]
    except:
        play_url_cut = play_url

    if play_url_cut.endswith(vod_ext):
        return play_label, play_url

    st = "TSDOWNLOADER"

    if ".m3u8" in play_url:
        st = "HLSRETRY"

    play_url = "plugin://plugin.video.f4mTester/?url=" + play_url + "&streamtype=" + st + "&name=" + play_label

    return play_label, play_url


def get_tl_tv(url):
    import base64
    import re
    import json
    from resources.lib import packer

    try:
        import urllib.parse as urllib
    except ImportError:
        import urllib

    client = HttpClient()
    if base64.b64decode('aHR0cHM6Ly90ZWxlcml1bS50dg==').decode("utf-8") not in url:
        req = client.get_request(url)
        tl_url = re.compile(r"<iframe .*?src='([^']+)'", re.DOTALL).findall(req.text)[0]
    else:
        tl_url = url

    rnd = re.compile(r'.*?/([\d]+)\.html', re.DOTALL).findall(tl_url)[0]

    req2 = client.get_request(tl_url)

    packed = re.compile(r'(eval\(function\(p,a,c,k,e,d\).*)').search(req2.text)
    if packed:
        unpacker = packer.jsUnpacker()
        unpacked = unpacker.unpack(packed.group(1))

        # Get the Token URL
        ajax_regex = r'{url:.*?atob\((\w*?)\).slice\((\w*?)\).*?\+.*?atob\((\w*?)\),dataType\s*:\s*[\'\"]json[\'\"]'
        vars = re.compile(ajax_regex).findall(unpacked)[0]

        p1 = re.compile(r'{0}\s*=\s*[\'\"](.+?)[\'\"];'.format(vars[0])).findall(unpacked)[0]
        p2 = re.compile(r'{0}\s*=\s*(\d+);'.format(vars[1])).findall(unpacked)[0]
        p3 = re.compile(r'{0}\s*=\s*[\'\"](.+?)[\'\"];'.format(vars[2])).findall(unpacked)[0]
        # slice = base64.b64decode(p2).decode("utf-8")
        part1 = base64.b64decode(p1)[int(p2):].decode("utf-8")
        part2 = base64.b64decode(p3).decode("utf-8")
        # logger.debug("part1 + part2: " + part1 + part2)
        cookie_regex = r'document.cookie.indexOf.*?compareProducts\(\"(.*?)\",([\d]+),'

        cookie_key, cookie_val = re.compile(cookie_regex, re.DOTALL).findall(unpacked)[0]
        base_url = base64.b64decode('aHR0cHM6Ly90ZWxlcml1bS50dg==').decode("utf-8")
        # Get the real token
        token_url = base_url + "/" + part1 + part2
        print(token_url)

        headers = {
            'Referer': tl_url,
        }

        cookies = {
            cookie_key: cookie_val,
        }

        json_token = client.get_request(token_url, headers=headers, cookies=cookies)

        # logger.debug("tokenJson: " + json_token)
        # print("tokenJson: " + json_token.text)
        s_json_token = json.loads(json_token.text)
        vars_part = re.compile(r'streamdelay=.*?;(.*?)function', re.S).findall(unpacked)[0]

        vars_part = vars_part.replace("var ", "").replace(";", "\n")
        var_pos = re.compile(r'=dameVuelta\(.*?\[(.*?)\]', re.MULTILINE).findall(unpacked)[0]

        exec(vars_part)
        pos = eval(var_pos)

        if s_json_token:
            html_token = s_json_token[int(pos)][::-1]
            # logger.debug("tokenHtml " + html_token)

        # Get the real CDN Url
        is_cdn = re.compile(r'if\(esMobiliar\){(\w*?)=.*?\};').findall(unpacked)
        if is_cdn:
            cdn_reversed = re.compile(r'{0}\s*=\s*[\'\"](.+?)[\'\"];'.format(is_cdn[0])).findall(unpacked)[0]
            cdn = base64.b64decode(cdn_reversed).decode("utf-8")
            # logger.debug("cdn: " + cdn)

        # Parse the final URL
        stream = 'https:{0}{1}|Referer={2}&User-Agent={3}&Origin={4}&Connection=keep-alive&Accept=*/*'
        u = stream.format(cdn, html_token + rnd, urllib.quote(tl_url, safe=''), client.headers["user-agent"],
                          base64.b64decode('aHR0cHM6Ly90ZWxlcml1bS50dg==').decode("utf-8"))

        return u


def db_strm(url):
    import re
    import base64
    try:
        client = HttpClient()
        r = client.get_request(url)
        iframe = re.compile(r'<iframe.*?src=\"([^\"]+)\"', re.MULTILINE | re.S).findall(r.text)[0]

        r = client.get_request(iframe, headers={"Referer": url})
        regex = r" = \[(.*)\]"
        rSI = ""
        tlc = re.compile(regex, re.MULTILINE | re.S).findall(r.text)[0]

        tlc = re.sub(r'\s', '', tlc)
        tlc = re.sub(r'\'', '', tlc)
        tlc = re.sub(r'\"', '', tlc)
        tlc = tlc.split(",")
        tlc = list(map(lambda x: x.strip("'"), tlc))

        mn = re.compile(r"\)\) - (\d+)\);", re.MULTILINE).findall(r.text)[0].strip()
        mn = int(mn)
        for s in tlc:
            b64 = base64.b64decode(s).decode("utf-8")
            n_str = re.sub(r'\D', '', b64)
            print(n_str)
            if n_str:
                str_n = int(n_str)
                str_n -= mn
                rSI += chr(str_n)

        play_url = re.compile(r"source.*?'(.*?)'", re.MULTILINE).findall(rSI)[0]

        return play_url + "|Referer=" + iframe
    except:
        return None


def m3u2xml(src):
    import re
    regex = r'#EXTINF:.*?tvg-logo=\"([^\"]+|)\".*?,(.*?)$\s(http.*?//.*?)$'

    matches = re.compile(regex, re.MULTILINE).findall(src)
    xml = ""

    for match in matches:
        title = str(match[1]).strip()
        img = str(match[0]).strip()
        link = str(match[2]).strip()
        type = "extsrc" if link.endswith(".m3u") else ""
        xml += "<item>"
        xml += "<title>" + title + "</title>" \
                                   "<link type=\"" + type + "\">" + link + "</link>" \
                                                                           "<plot>" + title + "</plot>" \
                                                                                              "<thumbnail>" + img + "</thumbnail>"
        xml += "</item>"

    return xml
