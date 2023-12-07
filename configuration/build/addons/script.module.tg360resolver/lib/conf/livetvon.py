from conf.common import CommonResolver


class Livetvon(CommonResolver):

    def find_page(self):
        return [r'<iframe src=\"([^\"]+)\".*?allow=']

    def set_referer(self, url):
        ref = self.resolver.find_hostname(self.resolver.stack[-1])
        return "!Referer=" + ref + "/&Origin=" + ref + "&user-agent=" + self.resolver.cli.headers["user-agent"]
