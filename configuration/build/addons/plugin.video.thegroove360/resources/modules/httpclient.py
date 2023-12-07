from resources.lib import kodiutils
from resources.lib.requests_doh import DNSOverHTTPSSession
import requests


class HttpClient:
    headers = {
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'accept': '*/*'
    }

    def __init__(self):
        self.headers["user-agent"] = self.get_random_ua()
        if kodiutils.get_setting_as_int("use_doh_requests"):
            dns = kodiutils.get_setting("dns_provider")
            self.session = DNSOverHTTPSSession(provider=dns)
        else:
            self.session = requests.session()

    def get_request(self, url, **kwargs):
        if "headers" not in kwargs:
            kwargs["headers"] = {}

        request_headers = self.headers
        request_headers.update(kwargs["headers"])
        kwargs["headers"] = request_headers
        if "timeout" not in kwargs:
            kwargs["timeout"] = 15

        gr = self.session.get(url, **kwargs)

        return gr

    def get_file(self, url, **kwargs):
        kwargs["stream"] = True

        return self.get_request(url, **kwargs)

    @staticmethod
    def get_random_ua():
        import json
        import random
        import os
        dir_path = os.path.dirname(os.path.realpath(__file__))

        with open(os.path.join(dir_path, 'UA.json'), 'r') as f:
            uas = json.load(f)

        return random.choice(uas)["ua"]
