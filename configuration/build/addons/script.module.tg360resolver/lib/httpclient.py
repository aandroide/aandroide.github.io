import requests
import logging
import xbmcaddon

import cloudscraper

logger = logging.getLogger(xbmcaddon.Addon().getAddonInfo('id'))


class HttpClient:

    headers = {
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'Connection': 'keep-alive',
        'accept': '*/*'
    }

    def __init__(self):
        self.headers["user-agent"] = self.get_random_ua()
        # self.session = requests.Session()
        self.session = cloudscraper.CloudScraper()

    def get_request(self, url, is_post=False, **kwargs):
        if "headers" not in kwargs:
            kwargs["headers"] = {}

        request_headers = self.headers
        request_headers.update(kwargs["headers"])
        kwargs["headers"] = request_headers
        if "timeout" not in kwargs:
            kwargs["timeout"] = 15

        if not is_post:
            if "hesgoal.com" in url:
                gr = requests.get(url)
            else:
                gr = self.session.get(url, **kwargs)
        else:
            gr = self.session.post(url, **kwargs)

        logger.debug("----------------------- REQUEST ------------------")
        logger.debug(gr.request.url)
        logger.debug(gr.request.headers)
        logger.debug(gr.headers)
        logger.debug(gr.status_code)
        logger.debug("\n" + gr.text)
        logger.debug("--------------------------------------------------")

        return gr

    def post_request(self, url, data=None, **kwargs):
        if data is None:
            data = {}

        kwargs["data"] = data
        return self.get_request(url, is_post=True, **kwargs)

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
