#{
#    "Id": "ListID",
#    "Name": "ListName",
#}

#
#     import json
#
#     result = M3UGroupItemfromdict(json.loads(json_string))

import uuid, json
from typing import List, Any, TypeVar, Callable, Type, cast
from lib import logger

T = TypeVar("T")


#def from_str(x: Any) -> str:
#    assert isinstance(x, str)
#    return x


#def from_bool(x: Any) -> bool:
#    assert isinstance(x, bool)
#    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    if not isinstance(x, list): logger.error("Not instance x list:", x)
    #assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    if not isinstance(x, c): logger.error("Not instance:", x)
    #assert isinstance(x, c)
    return cast(Any, x).to_dict()


class M3UGroupItem:
    Id: str
    Name: str
    Description: str

    def __init__(self, Id: str = "", Name: str = "", Description: str = "") -> None:
        if not Id: Id = self.__get_newid()
        if not Description: Description = Name
        self.Id   = Id
        self.Name = Name
        self.Description = Description

    def __get_newid(self):
        iDs = str(uuid.uuid4()).split("-")
        uId = iDs[0] + iDs[1] + iDs[2]
        return uId

    @staticmethod
    def from_dict(obj: Any) -> 'M3UGroupItem':
        if not isinstance(obj, dict): logger.error("Not a dict:", obj)
        #assert isinstance(obj, dict)
        Id   = obj.get("Id", "")
        Name = obj.get("Name", "")
        Description = obj.get("Description", "")

        return M3UGroupItem(Id, Name, Description)

    def to_dict(self) -> dict:
        result: dict = dict()
        result["Id"]   = self.Id
        result["Name"] = self.Name
        result["Description"] = self.Description
        return result

    def to_json(self) -> str:
        result = json.dumps(self.to_dict())
        return result


def M3UGroupItemfromdict(s: Any) -> M3UGroupItem:
    return M3UGroupItem.from_dict(s)


def M3UGroupItemtodict(x: M3UGroupItem) -> Any:
    return to_class(M3UGroupItem, x)
