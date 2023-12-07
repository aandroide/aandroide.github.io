from conf.common import CommonResolver


class Calcio(CommonResolver):

    def set_referer(self, url):
        return "!Referer=" + self.resolver.find_hostname(self.resolver.start_url)
        
    def find_stream(self):
        return [r" source:\s\"([^\"]+)\","]
