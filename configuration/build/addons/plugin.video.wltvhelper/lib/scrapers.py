# -*- coding: utf-8 -*-
import re

def findSingleMatch(data, pattern, index=0, flags=re.DOTALL):
    try:
        if index == 0:
            matches = re.search(pattern, data, flags=flags)
            if matches:
                groupslen = len(matches.groups())
                if groupslen == 1:
                    return matches.group(1)
                elif groupslen > 1:
                    return matches.groups()
                else:
                    return matches.group()
            else:
                return ""
        else:
            matches = re.findall(pattern, data, flags=flags)
            return matches[index]
    except:
        return ""


def findMultipleMatches(text, pattern, flags=re.DOTALL):
    return re.findall(pattern, text, flags=flags)

def findMultipleGroups(text, pattern, flags=re.DOTALL):
    return [x for xs in re.findall(pattern, text, flags=flags) for x in xs]
