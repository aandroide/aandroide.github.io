#[
#    {
#        "Name": "CustomListName",
#        "Id": "ListID",
#        "Lists": [ M3UList_object ]
#    }
#]

#     import json
#
#     result = CustomListfromdict(json.loads(json_string))

import json, uuid
from enum import Enum
from typing import List, Any, TypeVar, Callable, Type, cast
from lib.m3u.m3ulist import M3UList
from lib import logger


T = TypeVar("T")


#def from_str(x: Any) -> str:
#    assert isinstance(x, str)
#    return x


#def from_bool(x: Any) -> bool:
#    assert isinstance(x, bool)
#    return x


#def from_enum(x: Any) -> str:
#    assert isinstance(x, ListType)
#    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    if not isinstance(x, list): logger.error("Not instance x list:", x)
    #assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    if not isinstance(x, c): logger.error("Not instance:", x)
    #assert isinstance(x, c)
    return cast(Any, x).to_dict()

class ListType(Enum):
    Emergency = 0
    Official  = 1
    Personal  = 2
    User      = 3
    Undefined = 99
    
    def __str__(self):
        return self.name


class CustomList:
    Id: str
    Name: str
    TypeOfList: ListType
    Lists: List[M3UList]

    def __init__(self, Id: str, Name: str, TypeOfList: ListType, Lists: List[M3UList] = None) -> None:
        if not Id: Id = self.__get_newid()
        if not Lists: Lists = list()
        self.Id   = Id
        self.Name = Name
        self.TypeOfList = TypeOfList
        self.Lists = Lists

    def index(self, obj: M3UList) -> int:
        return self.Lists.index(obj)

    @staticmethod
    def from_dict(obj: Any) -> 'CustomList':
        if not isinstance(obj, dict): logger.error("Not a dict:", obj)
        #assert isinstance(obj, dict)
        Id   = obj.get("Id", "")
        Name = obj.get("Name", "")
        TypeOfList = ListType(int(obj.get("TypeOfList", 99)))
        Lists = from_list(M3UList.from_dict, obj.get("Lists", list()))
        return CustomList(Id, Name, TypeOfList, Lists)

    def to_dict(self) -> dict:
        result: dict = dict()
        result["Id"]   = self.Id
        result["Name"] = self.Name
        result["TypeOfList"] = self.TypeOfList.value
        result["Lists"] = from_list(lambda x: to_class(M3UList, x), self.Lists)
        return result

    def __get_newid(self):
        iDs = str(uuid.uuid4()).split("-")
        uId = iDs[0]+iDs[1]+iDs[2]
        return uId


def CustomListfromdict(s: Any) -> List[CustomList]:
    return from_list(CustomList.from_dict, s)

def CustomListtodict(x: List[CustomList]) -> Any:
    return from_list(lambda x: to_class(CustomList, x), x)

def CustomListfromjson(s: Any) -> List[CustomList]:
    return from_list(CustomList.from_dict, json.loads(s))