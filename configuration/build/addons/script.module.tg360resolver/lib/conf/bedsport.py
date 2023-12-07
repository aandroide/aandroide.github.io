import re

from conf.common import CommonResolver


class Bedsport(CommonResolver):

    def find_page_src(self, src):
        fid = re.compile(r"fid='([^']+)';", re.MULTILINE).findall(src)[0]

        iframe = "https://ragnaru.net/embed.php?player=desktop&live=" + fid

        return "<iframe src='" + iframe + "'>"
