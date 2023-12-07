import inspect
import json
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from resolver_360 import SportResolver


class CommonResolver:

    def __init__(self, resolver: 'SportResolver'):
        self.servers = self.set_servers()
        self.resolver = resolver
        self.page_url = None
        self.page_src = None
        self.request_headers = {}
        self.set_request_headers()
        self.use_last_domain = False

    def set_request_headers(self):
        pass

    def set_page_url(self, url):
        self.page_url = url

    def set_page_src(self, page_src):
        self.page_src = page_src

    def set_servers(self):
        try:
            fpath = inspect.getfile(self.__class__)
            jsonf = re.sub(r"^(.*?\.)(py)$", "\\1json", fpath, 0, re.DOTALL)
            with open(jsonf, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data["domains"]
        except Exception as E:
            print(E)
            import traceback
            traceback.print_stack()
            return []

    def find_page(self):
        pass

    def find_page_src(self, src):
        pass

    def parse_stream(self, url):
        pass

    def set_referer(self, url):
        pass

    def find_stream(self):
        pass
