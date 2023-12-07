from conf.common import CommonResolver


class Skystreaming(CommonResolver):

    def set_referer(self, url):
        return "!Referer=" + self.resolver.find_hostname(self.resolver.start_url)

    def find_stream(self):
        return [r"<source src=\"([^\"]+)\"\s"]
