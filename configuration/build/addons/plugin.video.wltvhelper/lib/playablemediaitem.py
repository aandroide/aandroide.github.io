# -*- coding: utf-8 -*-
# 
#     import json
#
#     result = PlayableMediaItemfromdict(json.loads(json_string))

from typing import Any, List, TypeVar, Callable, Type, cast
from lib import logger

T = TypeVar("T")


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    if not isinstance(x, c): logger.error("Not instance:", x)
    return cast(Any, x).to_dict()


class PlayableMediaItem:
    Id: int
    EpisodeId: int

    Title:   str
    Season:  int
    Episode: int
    EpisodeTitle: str

    Plot:      str
    Thumbnail: str
    Fanart:    str
    
    Link:      str
    IsFilm:    bool
    IsExternalLink: bool


    def __init__(self, 
                 Id:int, EpisodeId:int, Title:str, 
                 Season:int, Episode:int, EpisodeTitle:str, 
                 Plot:str, Thumbnail:str, Fanart:str, 
                 Link:str, IsFilm:bool, IsExternalLink:bool=False) -> None:
        
        if not Id           : Id        = 0
        if not EpisodeId    : EpisodeId = 0
        if not Title        : Title     = ""
        if not Season       : Season    = 1
        if not Episode      : Episode   = 0
        if not EpisodeTitle : EpisodeTitle = ""
        if not Plot         : Plot      = ""
        if not Thumbnail    : Thumbnail = ""
        if not Fanart       : Fanart    = ""
        if not Link         : Link      = ""

        self.Id           = Id
        self.EpisodeId    = EpisodeId
        self.Title        = Title    .strip()
        self.Season       = Season
        self.Episode      = Episode
        self.EpisodeTitle = EpisodeTitle.strip()
        self.Plot         = Plot     .strip()
        self.Thumbnail    = Thumbnail.strip()
        self.Fanart       = Fanart   .strip()
        self.Link         = Link     .strip()
        self.IsFilm       = IsFilm
        self.IsExternalLink = IsExternalLink


    @staticmethod
    def from_dict(obj: Any) -> 'PlayableMediaItem':
        if not isinstance(obj, dict): logger.error("Not a dict:", obj)

        Id        = obj.get("Id",        0)
        EpisodeId = obj.get("EpisodeId", 0)
        Title     = obj.get("Title",     "")
        Season    = obj.get("Season",    0)
        Episode   = obj.get("Episode",   0)
        EpisodeTitle = obj.get("EpisodeTitle", "")
        Plot      = obj.get("Plot",      "")
        Thumbnail = obj.get("Thumbnail", "")
        Fanart    = obj.get("Fanart",    "")
        Link      = obj.get("Link",      "")
        IsFilm    = obj.get("IsFilm",    False)
        IsExternalLink = obj.get("IsExternalLink", False)

        return PlayableMediaItem(Id, EpisodeId, Title, Season, Episode, EpisodeTitle, Plot, Thumbnail, Fanart, Link, IsFilm, IsExternalLink)

        
    def to_dict(self) -> dict:
        result: dict = dict()
        result["Id"]         = self.Id
        result["EpisodeId"]  = self.EpisodeId
        result["Title"]      = self.Title
        result["Season"]     = self.Season
        result["Episode"]    = self.Episode
        result["EpisodeTitle"] = self.EpisodeTitle
        result["Plot"]       = self.Plot
        result["Thumbnail"]  = self.Thumbnail
        result["Fanart"]     = self.Fanart
        result["Link"]       = self.Link
        result["IsFilm"]     = self.IsFilm
        result["IsExternalLink"] = self.IsExternalLink
        
        return result

    
    def IsValid(self) -> bool:
        return self.Title and self.Link

    
    def GetTitle(self) -> str:
        return self.Title if self.IsFilm or self.IsExternalLink else f"{str(self.Season)}x{str(self.Episode).zfill(2)} - {self.EpisodeTitle}"


def PlayableMediaItemfromdict(s: Any) -> List[PlayableMediaItem]:
    return from_list(PlayableMediaItem.from_dict, s)


def PlayableMediaItemtodict(x: List[PlayableMediaItem]) -> Any:
    return from_list(lambda x: to_class(PlayableMediaItem, x), x)
