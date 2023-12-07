# -*- coding: utf-8 -*-

#class BroadcasterResult:
#    def __init__(self):
#        self.Url = ""
#        self.Subtitles = []
#        self.ManifestType = ""
#        self.LicenseKey   = ""
#        self.LicenseType  = "com.widevine.alpha"
#        self.ManifestUpdateParameter = ""
#        self.StreamHeaders = ""

# -*- coding: utf-8 -*-

class BroadcasterResult(object):
    Title = ""
    Url = None
    Subtitles = []
    ManifestType = ""
    LicenseKey   = ""
    LicenseType  = "com.widevine.alpha"
    ManifestUpdateParameter = ""
    StreamHeaders = ""
    ManifestHeaders = ""
    StreamSelectionType = ""
    Delay = 0
    PlayerMode = 0
    PlayableMediaItems = None

    def __init__(self, dic={}, **kwargs):
        self.fromdict(dic)
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def __str__(self):
        """
        Returns the object as a formatted string "key = value".
        For debugging purposes.
        """
        return "\n\t{}".format("\n\t".join("{} = {}".format(k, v) for k, v in self.todict().items())) # For Print
        # return "\r\t{}".format("\r\t".join("{} = {}".format(k, v) for k, v in self.todict().items())) # For Kodi Log

    def __getattr__(self, name):
        """
        Returns the default values in case the requested attribute does not exist in the item
        """

        if name.startswith("__"):
            return super(BroadcasterResult, self).__getattribute__(name)

        # default value for all other attributes
        else:
            return ""

    def clone(self, **kwargs):
        """
        Generate a new item by cloning the current item
        Applications: NewItem = item.clone()
                      NuewItem = item.clone(title='New Title', action = 'New Action')
        """
        import copy
        newitem = copy.deepcopy(self)
        for kw in kwargs:
            newitem.__setattr__(kw, kwargs[kw])

        return newitem

    def todict(self):
        """
        Generate a dict from current object
        """
        dic = self.__dict__.copy()

        ret = dict()
        for k in sorted(dic):
            if isinstance(dic[k], BroadcasterResult):
                ret[k] = dic[k].todict()
            else:
                ret[k] = dic[k]

        return ret

    def fromdict(self, dic):
        """
        Generate Object from current dict
        """
        for k, v in dic.items():
            self.__setattr__(k, v)
        return self

