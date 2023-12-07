#
#     import json
#
#     result = M3UItemfromdict(json.loads(json_string))

import re
from typing import Any, List, TypeVar, Callable, Type, cast
from lib import logger

T = TypeVar("T")

TAG_TVG_NAME = "tvg-name"
TAG_TVG_CHNO = "tvg-chno"
TAG_TVG_ID   = "tvg-id"
TAG_TVG_LOGO = "tvg-logo"
TAG_GROUP_TITLE = "group-title"
TAG_TVG_YEAR = "tvg-year"  
TAG_TVG_GENRES = "tvg-genres"

TAG_USER_AGENT  = "user-agent"

#def from_str(x: Any) -> str:
#    assert isinstance(x, str)
#    return x


#def from_int(x: Any) -> int:
#    assert isinstance(x, int) and not isinstance(x, bool)
#    return x


#def from_bool(x: Any) -> bool:
#    assert isinstance(x, bool)
#    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    #assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    if not isinstance(x, c): logger.error("Not instance:", x)
    #assert isinstance(x, c)
    return cast(Any, x).to_dict()


class M3UItem:
    Title:    str
    TvgName:  str
    TvgChNo:  int
    TvgId:    str
    TvgLogo:  str
    TvgGroup: str

    TvgYear:  int
    TvgGenres:list

    UserAgent:str
    Referer:  str
    Link:     str
    IsFilm:   bool
    IsSerie:  bool
    IsLive:   bool
    IsKaraoke:bool


    def __init__(self, Title: str, TvgName: str, TvgChNo: int, TvgId: str, TvgLogo: str, TvgGroup: str, TvgYear: int, TvgGenres: list, UserAgent: str, Referer: str, Link: str, IsFilm: bool, IsSerie: bool, IsLive: bool, IsKaraoke: bool) -> None:
        if not TvgName:   TvgName  = Title
        if not TvgChNo:   TvgChNo  = 0
        if not TvgId:     TvgId    = Title.lower()
        if not TvgLogo:   TvgLogo  = ""
        if not TvgGroup:  TvgGroup = "Unknown"
        if not TvgYear:   TvgYear  = 0
        if not TvgGenres: TvgGenres   = list()

        if not UserAgent: UserAgent= ""
        if not Referer:   Referer  = ""

        self.Title    = Title    .strip()
        self.TvgName  = TvgName  .strip()
        self.TvgChNo  = TvgChNo
        self.TvgId    = TvgId    .strip()
        self.TvgLogo  = TvgLogo  .strip()
        self.TvgGroup = TvgGroup .strip()

        self.TvgYear  = TvgYear
        self.TvgGenres = TvgGenres

        self.UserAgent= UserAgent.strip()
        self.Referer  = Referer  .strip()
        self.Link     = Link     .strip()
        self.IsFilm   = IsFilm
        self.IsSerie  = IsSerie
        self.IsLive   = IsLive
        self.IsKaraoke= IsKaraoke


    @staticmethod
    def from_dict(obj: Any) -> 'M3UItem':
        if not isinstance(obj, dict): logger.error("Not a dict:", obj)
        #assert isinstance(obj, dict)
        Title    = obj.get("Title",    "")
        TvgName  = obj.get("TvgName",  "")
        TvgChNo  = obj.get("TvgChNo",  0)
        TvgId    = obj.get("TvgId",    "")
        TvgLogo  = obj.get("TvgLogo",  "")
        TvgGroup = obj.get("TvgGroup", "")

        TvgYear  = obj.get("TvgYear",  0)
        TvgGenres= obj.get("TvgGenres",  ())

        UserAgent= obj.get("UserAgent","")
        Referer  = obj.get("Referer",  "")
        Link     = obj.get("Link",     "")
        IsFilm   = obj.get("IsFilm",    False)
        IsSerie  = obj.get("IsSerie",   False)
        IsLive   = obj.get("IsLive",    False)
        IsKaraoke= obj.get("IsKaraoke", False)

        return M3UItem(Title, TvgName, TvgChNo, TvgId, TvgLogo, TvgGroup, TvgYear, TvgGenres, UserAgent, Referer, Link, IsFilm, IsSerie, IsLive, IsKaraoke)

    @staticmethod
    def from_extinf_url(extInf: str, url: str) -> None:
        if(extInf and url):
            try:
                m = re.search( TAG_TVG_NAME + '="(.*?)"', extInf)
                tvg_name = m.group(1) if m else ""
                m = re.search( TAG_TVG_CHNO + '="(.*?)"', extInf)
                tvg_ch_no = m.group(1) if m else ""
                m = re.search( TAG_TVG_ID   + '="(.*?)"', extInf)
                tvg_id = m.group(1) if m else ""
                m = re.search( TAG_TVG_LOGO + '="(.*?)"', extInf)
                tvg_logo = m.group(1) if m else ""
                m = re.search( TAG_GROUP_TITLE + '="(.*?)"', extInf)
                tvg_group = m.group(1) if m else ""

                m = re.search( TAG_TVG_YEAR + '="(.*?)"', extInf)
                tvg_year = m.group(1) if m else ""
                m = re.search( TAG_TVG_GENRES + '="(.*?)"', extInf)
                tmp_genres = m.group(1) if m else ""
                tvg_genres = list()
                if tmp_genres:
                    tvg_genres = tmp_genres.split('-')

                m = re.search( TAG_USER_AGENT  + '="(.*?)"', extInf)
                user_agent = m.group(1) if m else ""
                #m = re.search("(?!.*=\",?.*\")[,](.*?)$", extInf)
                #title = m.group(1)
                
                title = ""
                splitted = extInf.split(',')
                if len(splitted) > 1:
                    title = splitted[-1]

                link = url

                is_film  = "/movie/"  in link.lower() or tvg_group.lower().startswith("movie") or tvg_group.lower().startswith("film")
                is_serie = "/series/" in link.lower() or tvg_group.lower().startswith("serie")
                is_karaoke = tvg_group.lower().startswith("kar")
                is_live  = (not is_serie and not is_film and not is_karaoke) or tvg_group.lower().startswith("live")

                return M3UItem(title, tvg_name, tvg_ch_no, tvg_id, tvg_logo, tvg_group, tvg_year, tvg_genres, user_agent, "", link, is_film, is_serie, is_live, is_karaoke)
            except Exception as ex :
                logger.error(ex)
                logger.error(extInf)
        
    def to_dict(self) -> dict:
        result: dict = dict()
        result["Title"]    = self.Title
        result["TvgName"]  = self.TvgName
        result["TvgChNo"]  = self.TvgChNo
        result["TvgId"]    = self.TvgId
        result["TvgLogo"]  = self.TvgLogo
        result["TvgGroup"] = self.TvgGroup

        result["TvgYear"] = self.TvgYear
        result["TvgGenres"]= self.TvgGenres

        result["UserAgent"]= self.UserAgent
        result["Referer"]  = self.Referer
        result["Link"]     = self.Link
        result["IsFilm"]   = self.IsFilm
        result["IsSerie"]  = self.IsSerie
        result["IsLive"]   = self.IsLive
        result["IsKaraoke"]= self.IsKaraoke
        
        return result

    def IsValid(self) -> bool:
        return self.Title and self.Link

def M3UItemfromdict(s: Any) -> List[M3UItem]:
    return from_list(M3UItem.from_dict, s)


def M3UItemtodict(x: List[M3UItem]) -> Any:
    return from_list(lambda x: to_class(M3UItem, x), x)
