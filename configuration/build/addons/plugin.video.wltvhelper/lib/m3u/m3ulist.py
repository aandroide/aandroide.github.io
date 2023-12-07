import uuid
from typing import List, Any, TypeVar, Callable, Type, cast
from lib import logger

T = TypeVar("T")
ALL_GROUPS_SELECTED = "*"

def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    if not isinstance(x, c): logger.error("Not instance:", x)
    return cast(Any, x).to_dict()

def getNormalized(listToNormalize) -> list:
    normalizedList = list()
    if isinstance(listToNormalize, dict):
        normalizedList = list(filter(lambda item: item.get("Name", "Unknown"), listToNormalize))
    elif isinstance(listToNormalize, list):
        normalizedList = listToNormalize
    elif isinstance(listToNormalize, str):
        normalizedList = [listToNormalize]

    return normalizedList

class M3UList:
    Id: str
    Name: str
    DisplayName: str
    Enabled: bool
    Tags: List[str]
    List: str
    Epg: str
    Groups: List[str]
    IsEmergency: bool
    IsUserList: bool
    IsPersonal: bool
    IsValid: bool
    #LastUpdate: date

    def __init__(self, Id: str = "", Name: str = "", DisplayName: str = "", Enabled: bool = False, Tags: List[str] = [], List: str = "", Epg: str = "", Groups: List[Any] = [], IsEmergency: bool = False, IsUserList: bool = False, IsPersonal: bool = False, IsValid: bool = False) -> None:
        if not Id: Id = self.__get_newid()
        if not DisplayName: DisplayName = Name
        
        normalizedGroup = getNormalized(Groups)
        
        self.Id      = Id
        self.Name    = Name
        self.DisplayName = DisplayName
        self.Enabled = Enabled
        self.Tags    = Tags
        self.List    = List
        self.Epg     = Epg
        self.Groups  = normalizedGroup
        self.IsEmergency = IsEmergency
        self.IsUserList  = IsUserList
        self.IsPersonal  = IsPersonal
        self.IsValid     = IsValid

    def AllGroupsSelected(self) -> bool:
        return self.Groups == [ALL_GROUPS_SELECTED] or self.Groups == []

    #def PartialGroupsSelected(self) -> bool:
    #    return self.Groups != [ALL_GROUPS_SELECTED] and len(self.Groups) > 0

    def __get_newid(self):
        iDs = str(uuid.uuid4()).split("-")
        uId = iDs[0]+iDs[1]+iDs[2]
        return uId

    @staticmethod
    def from_dict(obj: Any) -> 'M3UList':
        if not isinstance(obj, dict): logger.error("Not a dict:", obj)
        #assert isinstance(obj, dict)
        Id      = obj.get("Id",   "")
        Name    = obj.get("Name", "")
        DisplayName = obj.get("DisplayName", "")
        Enabled = obj.get("Enabled", False)
        Tags    = obj.get("Tags", list())
        List    = obj.get("List", "")
        Epg     = obj.get("Epg",  "")
        Groups  = obj.get("Groups", list())
        IsEmergency = obj.get("IsEmergency", False)
        IsUserList  = obj.get("IsUserList",  False)
        IsPersonal  = obj.get("IsPersonal",  False)
        IsValid     = obj.get("IsValid",     False)

        return M3UList(Id, Name, DisplayName, Enabled, Tags, List, Epg, Groups, IsEmergency, IsUserList, IsPersonal, IsValid)


    def to_dict(self) -> dict:
        result: dict = dict()
        result["Id"]          = self.Id
        result["Name"]        = self.Name
        result["DisplayName"] = self.DisplayName
        result["Enabled"]     = self.Enabled
        result["Tags"]        = self.Tags
        result["List"]        = self.List
        result["Epg"]         = self.Epg
        result["Groups"]      = self.Groups
        result["IsEmergency"] = self.IsEmergency
        result["IsUserList"]  = self.IsUserList
        result["IsPersonal"]  = self.IsPersonal
        result["IsValid"]     = self.IsValid
        return result


    def to_json(self) -> dict:
        return self.to_dict()


def M3UListfromdict(s: Any) -> M3UList:
    return M3UList.from_dict(s)


def M3UListtodict(x: M3UList) -> Any:
    return to_class(M3UList, x)
