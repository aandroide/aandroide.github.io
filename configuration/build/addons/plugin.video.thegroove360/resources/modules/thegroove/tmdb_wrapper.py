import re
import logging
import xbmcaddon
import xbmc
import xbmcvfs
import sys

import os
import json

from resources.lib import kodiutils
from resources.lib import tmdbsimple as tmdbapi

if kodiutils.get_setting("tmdb_api_key") == "":
    tmdbapi.API_KEY = '1079b0db191ed7925774c0388be1aa78'
else:
    tmdbapi.API_KEY = kodiutils.get_setting("tmdb_api_key")

logger = logging.getLogger(xbmcaddon.Addon().getAddonInfo('id'))


def tmdb(meta, li):
    logger.debug("________________ TMDB ________________")
    search = tmdbapi.Search()
    try:
        title = re.compile(r'<title>(.*?)</title>', re.S).findall(meta)[0]
        li_type = re.compile(r'<type>(.*?)</type>', re.S).findall(meta)[0].lower()
        year = ""
        if "year" in meta:
            try:
                year = re.compile(r'<year>(.*?)</year>', re.S).findall(meta)[0]
            except:
                year = ""
    except Exception as e:
        if kodiutils.get_setting_as_bool("debug"):
            import traceback
            traceback.print_stack()
            logger.debug(e)
        return li

    response = {}
    if li_type == "movie":
        response = search.movie(query=title, language="it-IT", year=year)

    if li_type == "tv":
        response = search.tv(query=title, language="it-IT")

    if "results" in response:
        try:
            res = response["results"][0]
        except:
            return li
        thumb = "https://image.tmdb.org/t/p/w185" + res["poster_path"]
        fanart = "https://image.tmdb.org/t/p/w300" + res["backdrop_path"]
        generi = genres(res["genre_ids"], type)
        plot = res["overview"]

        try:
            rating = float(res["vote_average"])
        except:
            rating = None

        try:
            if li_type == "movie":
                release = res["release_date"]
            else:
                release = res["first_air_date"]
        except:
            release = None

        if "thumb" not in li.arts or li.arts["thumb"] == "":
            li.arts["thumb"] = thumb

        if "fanart" not in li.arts or li.arts["fanart"] == "":
            li.arts["fanart"] = fanart

        if li.info["plot"] == "":
            li.info["plot"] = plot

        if generi:
            li.info["genre"] = generi.split(", ")

        if release:
            li.info["year"] = release[0:4]
            li.info["aired"] = release

        if rating:
            li.info["rating"] = rating

    return li


def genres(genres_ids, li_type):
    gens = tmdbapi.Genres()
    if sys.version_info[0] > 2:
        tmp = xbmcvfs.translatePath(u'special://temp/')
    else:
        tmp = xbmc.translatePath(u'special://temp/')

    if li_type == "movie":
        json_genres = os.path.join(tmp, "thegroove360_movies_genres.json")
    else:
        json_genres = os.path.join(tmp, "thegroove360_tv_genres.json")

    if os.path.exists(json_genres):
        with open(json_genres, 'r') as f:
            genres_list = json.load(f)
            f.close()
    else:
        genres_list = gens.movie_list(language="it-IT")
        with open(json_genres, 'w') as f:
            json.dump(genres_list, f)
            f.close()

    genres_obj = list(filter(lambda x: x["id"] in genres_ids, genres_list["genres"]))
    genres_label = map(lambda x: x["name"], genres_obj)

    return ", ".join(genres_label)
