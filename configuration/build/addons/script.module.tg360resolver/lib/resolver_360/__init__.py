import json
import os.path

from resolver_360.thegroove_sport_resolver import SportResolver
import logging
import xbmcaddon

logger = logging.getLogger(xbmcaddon.Addon().getAddonInfo('id'))


def resolve(url):
    sr = SportResolver(url)
    sr.find_page_src()

    if sr.resolved:
        logger.debug(sr.resolved_urls)
        return sr.resolved_urls

    return None


def update_domains(json_content):
    import pathlib

    for name in json_content:
        p = pathlib.Path(__file__).parent.resolve()
        confdir = os.path.join(p, "..", "conf")
        with open(os.path.join(confdir, name), 'w+') as outfile:
            outfile.write(json.dumps(json_content[name]))
            outfile.close()
