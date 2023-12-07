import sys
import xbmc

if __name__ == '__main__':
    xbmc.executebuiltin("RunPlugin({})".format(sys.listitem.getPath()))