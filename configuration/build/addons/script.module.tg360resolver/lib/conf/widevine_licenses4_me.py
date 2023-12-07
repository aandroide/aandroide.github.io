from conf.common import CommonResolver


class WidevineLicense4me(CommonResolver):

    def set_referer(self, url):
        return "!Referer=" + self.resolver.find_hostname(self.resolver.stack[-1])
