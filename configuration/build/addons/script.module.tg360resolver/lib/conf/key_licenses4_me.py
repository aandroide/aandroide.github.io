from conf.common import CommonResolver
import re
import urllib


class KeyLicenses4Me(CommonResolver):

    def set_request_headers(self):
        self.request_headers = {"referer": self.resolver.find_hostname(self.resolver.start_url) + "/"}

