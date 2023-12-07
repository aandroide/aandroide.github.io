from conf.common import CommonResolver


class Starlive(CommonResolver):

    def find_stream(self):
        return [r"var src=\"([^\"]+)\"", r"<iframe.*?src=\".*?\#(http.*?:\/\/.*?)\".*?>"]

    def set_referer(self, url):
        ref = self.resolver.find_hostname(self.resolver.stack[-1])
        return "!&origin=" + ref + "&user-agent=" + self.resolver.cli.headers["user-agent"]
