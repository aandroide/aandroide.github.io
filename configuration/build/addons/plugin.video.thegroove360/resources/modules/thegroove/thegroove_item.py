import logging
import xbmcaddon
import re

from resources.lib import kodilogging
from resources.modules.thegroove.thegroove_resolvers import resolvers as tg_resolvers

ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()

'''
genre	string (Comedy) or list of strings (["Comedy", "Animation", "Drama"])
country	string (Germany) or list of strings (["Germany", "Italy", "France"])
year	integer (2009)
episode	integer (4)
season	integer (1)
sortepisode	integer (4)
sortseason	integer (1)
episodeguide	string (Episode guide)
showlink	string (Battlestar Galactica) or list of strings (["Battlestar Galactica", "Caprica"])
top250	integer (192)
setid	integer (14)
tracknumber	integer (3)
rating	float (6.4) - range is 0..10
userrating	integer (9) - range is 1..10 (0 to reset)
watched	depreciated - use playcount instead
playcount	integer (2) - number of times this item has been played
overlay	integer (2) - range is 0..7. See Overlay icon types for values
cast	list (["Michal C. Hall","Jennifer Carpenter"]) - if provided a list of tuples cast will be interpreted as castandrole
castandrole	list of tuples ([("Michael C. Hall","Dexter"),("Jennifer Carpenter","Debra")])
director	string (Dagur Kari) or list of strings (["Dagur Kari", "Quentin Tarantino", "Chrstopher Nolan"])
mpaa	string (PG-13)
plot	string (Long Description)
plotoutline	string (Short Description)
title	string (Big Fan)
originaltitle	string (Big Fan)
sorttitle	string (Big Fan)
duration	integer (245) - duration in seconds
studio	string (Warner Bros.) or list of strings (["Warner Bros.", "Disney", "Paramount"])
tagline	string (An awesome movie) - short description of movie
writer	string (Robert D. Siegel) or list of strings (["Robert D. Siegel", "Jonathan Nolan", "J.K. Rowling"])
tvshowtitle	string (Heroes)
premiered	string (2005-03-04)
status	string (Continuing) - status of a TVshow
set	string (Batman Collection) - name of the collection
setoverview	string (All Batman movies) - overview of the collection
tag	string (cult) or list of strings (["cult", "documentary", "best movies"]) - movie tag
imdbnumber	string (tt0110293) - IMDb code
code	string (101) - Production code
aired	string (2008-12-07)
credits	string (Andy Kaufman) or list of strings (["Dagur Kari", "Quentin Tarantino", "Chrstopher Nolan"]) - writing credits
lastplayed	string (Y-m-d h:m:s = 2009-04-05 23:16:04)
album	string (The Joshua Tree)
artist	list (['U2'])
votes	string (12345 votes)
path	string (/home/user/movie.avi)
trailer	string (/home/user/trailer.avi)
dateadded	string (Y-m-d h:m:s = 2009-04-05 23:16:04)
mediatype	string - "video", "movie", "tvshow", "season", "episode" or "musicvideo"
dbid	integer (23) - Only add this for items which are part of the local db. You also need to set the correct 'mediatype'!
'''


class ThegrooveItem:

    def __init__(self, **kwargs):

        self._raw = ""

        self.arts = {"thumbnail": "", "fanart": ""}
        self.info = {"genre": "", "country": "", "year": "", "episode": "", "season": "", "sortepisode": "",
                     "sortseason": "", "episodeguide": "", "showlink": "", "top250": "", "setid": "", "tracknumber": "",
                     "rating": "", "userrating": "", "watched": "", "playcount": "", "overlay": "", "cast": [],
                     "castandrole": [], "director": "", "mpaa": "", "plot": "", "plotoutline": "", "title": "",
                     "originaltitle": "", "sorttitle": "", "duration": "", "studio": "", "tagline": "", "writer": "",
                     "tvshowtitle": "", "premiered": "", "status": "", "set": "", "setoverview": "", "tag": "",
                     "imdbnumber": "", "code": "", "aired": "", "credits": "", "lastplayed": "", "album": "",
                     "artist": [], "votes": "", "path": "", "trailer": "", "dateadded": "", "mediatype": "video",
                     "dbid": ""}
        self.regexes = []
        self.is_folder = True
        self.url = ""
        self.label = ""
        self.parent_xml = ""
        self.sublinks = []
        self.is_playable = False
        self.tg_resolver = ""
        self.is_plugin = False
        self.pos = 0

        self.__dict__.update(**kwargs)

    @staticmethod
    def get_thegroove_resolver(xml, url):
        try:
            tg_type = re.compile(r'type=\"([^\"]+)\"', re.MULTILINE | re.DOTALL).findall(xml)[0]
            if tg_type != "" and tg_type in tg_resolvers:
                return tg_type
        except IndexError:
            import json
            import os
            resolver_defs = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), "resources", "modules", "thegroove",
                                         "resolvers.json")
            with open(resolver_defs) as json_file:
                data = json.load(json_file)
                for s in data:
                    if any(x in url for x in data[s]["hosts"]):
                        return s

            return ""

    @staticmethod
    def convert_to_dict(obj):
        """
        A function takes in a custom object and returns a dictionary representation of the object.
        This dict representation includes meta data such as the object's module and class names.
        """

        #  Populate the dictionary with object meta data
        obj_dict = {
            "__class__": obj.__class__.__name__,
            "__module__": obj.__module__
        }

        #  Populate the dictionary with object properties
        obj_dict.update(obj.__dict__)

        return obj_dict

    @staticmethod
    def dict_to_obj(obj_dict):

        """
        Function that takes in a dict and returns a custom object associated with the dict.
        This function makes use of the "__module__" and "__class__" metadata in the dictionary
        to know which object type to create.
        """
        if "__class__" in obj_dict:
            # Pop ensures we remove metadata from the dict to leave only the instance arguments
            obj_dict.pop("__class__")

            # Get the module name from the dict and import it
            obj_dict.pop("__module__")

            # Use dictionary unpacking to initialize the object
            obj = ThegrooveItem(**obj_dict)
        else:
            obj = obj_dict
        return obj
