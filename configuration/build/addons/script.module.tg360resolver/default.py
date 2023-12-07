import sys
from lib import kodilogging
import logging
import xbmcaddon

ADDON = xbmcaddon.Addon()
kodilogging.config()

logger = logging.getLogger(xbmcaddon.Addon().getAddonInfo('id'))


def main(argv=None):
    if sys.argv:
        argv = sys.argv

    logger.debug(argv)


if __name__ == '__main__':
    sys.exit(main())
