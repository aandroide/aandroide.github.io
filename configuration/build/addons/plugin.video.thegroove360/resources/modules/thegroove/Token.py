import sys
l1l1ll_thegroove=sys.version_info[0]==2
l111_thegroove=2048
l1lll1_thegroove=7
def l1l1lll_thegroove(l1l_thegroove):
 global l1l11l_thegroove
 l11llll_thegroove=ord(l1l_thegroove[-1])
 ll_thegroove=l1l_thegroove[:-1]
 l1lll11_thegroove=l11llll_thegroove%len(ll_thegroove)
 l111l_thegroove=ll_thegroove[:l1lll11_thegroove]+ll_thegroove[l1lll11_thegroove:]
 if l1l1ll_thegroove:
  l1l1l11_thegroove=l11l11_thegroove().join([l1ll1l_thegroove(ord(char)-l111_thegroove-(l11ll_thegroove+l11llll_thegroove)%l1lll1_thegroove)for l11ll_thegroove,char in enumerate(l111l_thegroove)])
 else:
  l1l1l11_thegroove=str().join([chr(ord(char)-l111_thegroove-(l11ll_thegroove+l11llll_thegroove)%l1lll1_thegroove)for l11ll_thegroove,char in enumerate(l111l_thegroove)])
 return eval(l1l1l11_thegroove)
import base64
import hashlib
import os
import sys
import random
from Cryptodome.Cipher import AES
import inspect
from datetime import datetime
try:
 from zoneinfo import ZoneInfo
except:
 from backports.zoneinfo import ZoneInfo
try:
 import xbmc
 import xbmcaddon
 import xbmcgui
 import xbmcvfs
except:
 pass
class Token:
 def __init__(self):
  self.name=l1l1lll_thegroove(u"ࠣࡲ࡯ࡹ࡬࡯࡮࠯ࡸ࡬ࡨࡪࡵ࠮ࡵࡪࡨ࡫ࡷࡵ࡯ࡷࡧ࠶࠺࠵ࠨ࣏")
  self.token=l1l1lll_thegroove(u"ࠤ࣐ࠥ")
  self.l1llll_thegroove=l1l1lll_thegroove(u"ࠥ࠷࠸࠸ࡓࡆࡅࡕࡉ࡙ࡧࡢࡤ࠳࠵࠷࠹ࠨ࣑")
  self.l1l1ll1_thegroove=l1l1lll_thegroove(u"࡙ࠦ࡮ࡥࡨࡴࡲࡳࡻ࡫ࠠ࠴࠸࠳࣒ࠦ")
  self.result=l1l1lll_thegroove(u"ࠧࠨ࣓")
  self.l1ll_thegroove=0
 def l1l1111_thegroove(self):
  __caller__=inspect.stack()[1].function
  self.l11l1l_thegroove(__caller__)
  l11llllll_thegroove=l1l1lll_thegroove(u"ࠨࡅࡶࡴࡲࡴࡪ࠵ࡒࡰ࡯ࡨࠦࣔ")
  l11lll1l1_thegroove=datetime.now(ZoneInfo(l11llllll_thegroove))
  l1l111l11_thegroove=datetime.timestamp(l11lll1l1_thegroove)
  return int(l1l111l11_thegroove)
 def l11111_thegroove(self,l1ll111_thegroove):
  __caller__=inspect.stack()[1].function
  self.l11l1l_thegroove(__caller__)
  l1l1l_thegroove=self.l1l1111ll_thegroove(l1l1lll_thegroove(u"ࠢࡪࡶࡨࡱࡤࡶࡡࡳࡵࡨࡶ࠳ࡶࡹࠣࣕ"))
  l1l1_thegroove=len(open(l1l1l_thegroove).read().splitlines())
  l11l_thegroove=l1ll111_thegroove%l1l1_thegroove
  self.l1ll_thegroove=l11l_thegroove
  return l11l_thegroove
 def l1l1111ll_thegroove(self,name):
  try:
   __addon__=xbmcaddon.Addon(id=self.name)
   if sys.version_info[0]<3:
    cwd=xbmc.translatePath(__addon__.getAddonInfo(l1l1lll_thegroove(u"ࠨࡲࡤࡸ࡭࠭ࣖ")))
   else:
    cwd=xbmcvfs.translatePath(__addon__.getAddonInfo(l1l1lll_thegroove(u"ࠩࡳࡥࡹ࡮ࠧࣗ")))
  except:
   cwd=os.getcwd()+l1l1lll_thegroove(u"ࠥ࠳ࡹ࡫ࡳࡵࠤࣘ")
  path=(l1l1lll_thegroove(u"ࠦࡷ࡫ࡳࡰࡷࡵࡧࡪࡹࠬ࡮ࡱࡧࡹࡱ࡫ࡳ࠭ࠤࣙ")+name).split(l1l1lll_thegroove(u"ࠧ࠲ࠢࣚ"))
  l1l1l_thegroove=cwd+os.sep+os.path.join(*path)
  return l1l1l_thegroove
 @staticmethod
 def l11ll1l_thegroove(l11l1ll_thegroove,l11l_thegroove):
  try:
   with open(l11l1ll_thegroove,l1l1lll_thegroove(u"࠭ࡲࠨࣛ"))as f:
    for line_number,line in enumerate(f):
     if line_number==l11l_thegroove:
      return str(line).strip()
  except Exception as e:
   pass
 def set_token(self):
  if not self.l11lll_thegroove():
   return None
  try:
   l1ll111_thegroove=self.l1l1111_thegroove()
   line=self.l11111_thegroove(l1ll111_thegroove)
   l11lll1ll_thegroove=str(len(str(line)))+str(line)
   n=(6-len(l11lll1ll_thegroove))
   l11llll1l_thegroove=pow(10,n-1)
   l1l111ll1_thegroove=pow(10,n)-1
   r=random.randint(l11llll1l_thegroove,l1l111ll1_thegroove)
   token=str(l1ll111_thegroove)+l1l1lll_thegroove(u"ࠢ࠯ࠤࣜ")+l11lll1ll_thegroove+str(r)
   self.token=base64.urlsafe_b64encode(token.encode(l1l1lll_thegroove(u"ࠣࡷࡷࡪ࠲࠾ࠢࣝ"))).decode()
   return line
  except Exception as e:
   import traceback
   traceback.print_stack()
   print(e)
   self.l1ll11_thegroove(l1l1lll_thegroove(u"ࠤࡉࡳࡷࡨࡩࡥࡦࡨࡲࠧࣞ"))
 def set_result(self,data):
  if not self.l11lll_thegroove():
   return None
  if data.headers and data.headers[l1l1lll_thegroove(u"ࠥࡘ࡭࡫ࡧࡳࡱࡲࡺࡪࠨࣟ")]==self.token:
   self.result=self.l11ll11_thegroove(data.text,self.l1ll_thegroove)
  else:
   self.l1ll11_thegroove(l1l1lll_thegroove(u"ࠦࡋࡵࡲࡣ࡫ࡧࡨࡪࡴࠢ࣠"))
   return None
 def l1l111l_thegroove(self,text):
  __caller__=inspect.stack()[1].function
  self.l11l1l_thegroove(__caller__)
  return None
 def l11ll11_thegroove(self,data,l1ll_thegroove):
  __caller__=inspect.stack()[1].function
  self.l11l1l_thegroove(__caller__)
  try:
   l1l1l_thegroove=self.l1l1111ll_thegroove(l1l1lll_thegroove(u"ࠧ࡯ࡴࡦ࡯ࡢࡴࡦࡸࡳࡦࡴ࠱ࡴࡾࠨ࣡"))
   l1l111l1l_thegroove=self.l11ll1l_thegroove(l1l1l_thegroove,l1ll_thegroove).rstrip().lstrip()
   if len(l1l111l1l_thegroove)<32:
    l1l111l1l_thegroove=l1l111l1l_thegroove.ljust(32,l1l1lll_thegroove(u"࠭ࠠࠨ࣢"))
   if len(l1l111l1l_thegroove)>32:
    l1l111l1l_thegroove=l1l111l1l_thegroove[0:32]
   l1l11111l_thegroove=str(hashlib.sha256(l1l111l1l_thegroove.encode(l1l1lll_thegroove(u"ࠢࡶࡶࡩ࠱࠽ࠨࣣ"))).hexdigest())
   l1l1l1_thegroove=l1l11111l_thegroove[:16]
   l1lll1l_thegroove=AES.new(l1l111l1l_thegroove.encode(l1l1lll_thegroove(u"ࠣࡷࡷࡪ࠲࠾ࠢࣤ")),AES.MODE_CFB,l1l1l1_thegroove.encode(l1l1lll_thegroove(u"ࠤࡸࡸ࡫࠳࠸ࠣࣥ")))
   result=l1lll1l_thegroove.decrypt(base64.urlsafe_b64decode(data.encode(l1l1lll_thegroove(u"ࠥࡹࡹ࡬࠭࠹ࠤࣦ"))+l1l1lll_thegroove(u"ࠦࡂࡃࠢࣧ").encode(l1l1lll_thegroove(u"ࠧࡻࡴࡧ࠯࠻ࠦࣨ"))))
   if str(l1ll_thegroove)==str(self.l1ll_thegroove):
    return result.decode(l1l1lll_thegroove(u"ࠨࡵࡵࡨ࠰࠼ࣩࠧ"))
   else:
    self.l1ll11_thegroove(l1l1lll_thegroove(u"ࠢࡆࡴࡵࡳࡷ࡫ࠠ࠵࠲࠸ࠦ࣪"),l1l1lll_thegroove(u"ࠣࡋࡰࡴࡴࡹࡳࡪࡤ࡬ࡰࡪࠦࡃࡰ࡯ࡳࡰࡪࡺࡡࡳࡧࠣࡐࡦࠦࡒࡪࡥ࡫࡭ࡪࡹࡴࡢࠤ࣫"))
  except Exception as e:
   self.l1ll11_thegroove(l1l1lll_thegroove(u"ࠤࡈࡶࡷࡵࡲࡦࠢ࠷࠴࠼ࠨ࣬"),l1l1lll_thegroove(u"ࠥࡍࡲࡶ࡯ࡴࡵ࡬ࡦ࡮ࡲࡥࠡࡅࡲࡱࡵࡲࡥࡵࡣࡵࡩࠥࡒࡡࠡࡔ࡬ࡧ࡭࡯ࡥࡴࡶࡤ࣭ࠦ"))
   import traceback
   traceback.print_stack()
   print(e)
  return None
 def l11lll_thegroove(self,skip=False):
  files=[l1l1lll_thegroove(u"ࠦࡹ࡮ࡥࡨࡴࡲࡳࡻ࡫ࠬࡵࡪࡨ࡫ࡷࡵ࡯ࡷࡧࡢ࡬ࡹࡺࡰࡤ࡮࡬ࡩࡳࡺ࠮ࡱࡻ࣮ࠥ"),l1l1lll_thegroove(u"ࠧ࡯ࡴࡦ࡯ࡢࡴࡦࡸࡳࡦࡴ࠱ࡴࡾࠨ࣯"),l1l1lll_thegroove(u"ࠨ࠮࠯࠮࡯࡭ࡧ࠲ࡰ࡭ࡷࡪ࡭ࡳ࠴ࡰࡺࠤࣰ")]
  l11lllll1_thegroove=[l1l1lll_thegroove(u"ࠢ࠹࠵࠸ࡩ࠷࡫࠲࠹ࡨ࠵ࡦࡩ࠷࠰࠲࠸࠻࠸ࡦ࠼࠰ࡧ࠲࠶ࡥ࠷ࡨࡢ࠷࠻ࡦ࠽ࡧ࠹ࡥ࠲ࡧ࠻ࡪ࠶ࡨࡤ࠷࠲ࡧ࠸࠽ࡩ࠶ࡥࡣ࠸࠺࠻࠺࠱ࡧࡣ࠻ࡥ࠼࠽ࡦࡢࠤࣱ"),l1l1lll_thegroove(u"ࠣ࠺࠸࠴࠺࠸ࡤࡥࡨ࠴࠼࠶࠹࠵ࡣࡧ࠶࠶ࡧ࠶࠹ࡢࡥ࠻ࡩ࠸࠾࠸ࡤࡧ࠻࠽࠹࠻࠳࠶ࡤࡩ࠺࠾࠾ࡥ࠵ࡣ࠳࠺࠺࠷࠶ࡤࡨ࠴ࡥࡩࡨ࠸ࡦ࠶ࡦ࠶ࡨ࠻࠱ࡣࡧࣲࠥ"),l1l1lll_thegroove(u"ࠤࡩ࠽࠵࠾ࡤ࠶࠳࠷࠹࠽࠷࠷࠲ࡦ࠻࠶ࡧࡨࡥ࠲ࡨ࠶࠸ࡨ࠻࠰ࡧ࠹࠻࠶࡫࠾ࡦࡦࡧ࠴࠺࠽࠷ࡣ࠺࠶࠶࠵࡫࠷ࡤ࠸ࡨ࠻ࡦ࠾࠷ࡥ࠸࠷࠳࠵ࡧ࠷ࡣ࠸ࡦࡩࠦࣳ")]
  for k,l1l111111_thegroove in enumerate(files):
   l1l1l_thegroove=self.l1l1111ll_thegroove(l1l111111_thegroove)
   try:
    with open(l1l1l_thegroove,l1l1lll_thegroove(u"ࠥࡶࡧࠨࣴ"))as f:
     l1l1111l1_thegroove=f.read()
     l11llll11_thegroove=hashlib.sha256(l1l1111l1_thegroove).hexdigest()
     if l11llll11_thegroove!=l11lllll1_thegroove[k]:
      print(l1l1l_thegroove+l1l1lll_thegroove(u"ࠦ࠿ࠦࠢࣵ")+l11llll11_thegroove+l1l1lll_thegroove(u"ࠧࠦ࠽࠿ࣶࠢࠥ")+l11lllll1_thegroove[k])
      raise Exception
   except Exception as e:
    self.l1ll11_thegroove(l1l1lll_thegroove(u"ࠨࡅࡳࡴࡲࡶࡪࠦ࠰ࠣࣷ"),l1l1lll_thegroove(u"ࠢࡇࡷࡱࡾ࡮ࡵ࡮ࡦࠢࡇ࡭ࡸࡶ࡯࡯࡫ࡥ࡭ࡱ࡫ࠠࡔࡱ࡯ࡳ࡙ࠥࡵࠣࣸ"),self.l1l1ll1_thegroove+l1l1lll_thegroove(u"ࠣࠢࡄࡨࡩࡵ࡮ࣹࠣ"))
    return False
  if skip is False:
   __caller__=inspect.stack()[1].function
   self.l11l1l_thegroove(__caller__)
  try:
   l11_thegroove=xbmc.getInfoLabel(l1l1lll_thegroove(u"ࠩࡆࡳࡳࡺࡡࡪࡰࡨࡶ࠳ࡖ࡬ࡶࡩ࡬ࡲࡓࡧ࡭ࡦࣺࠩ"))
   l11_thegroove=xbmcaddon.Addon(l11_thegroove).getAddonInfo(l1l1lll_thegroove(u"ࠪࡲࡦࡳࡥࠨࣻ"))
   if l11_thegroove!=self.l1l1ll1_thegroove:
    raise Exception()
  except Exception as e:
   self.l1ll11_thegroove(l1l1lll_thegroove(u"ࠦࡊࡸࡲࡰࡴࡨࠤ࠶ࠨࣼ"),l1l1lll_thegroove(u"ࠧࡌࡵ࡯ࡼ࡬ࡳࡳ࡫ࠠࡅ࡫ࡶࡴࡴࡴࡩࡣ࡫࡯ࡩ࡙ࠥ࡯࡭ࡱࠣࡗࡺࠨࣽ"),self.l1l1ll1_thegroove+l1l1lll_thegroove(u"ࠨࠠࡂࡦࡧࡳࡳࠨࣾ"))
   return False
  try:
   l1l11l1_thegroove=xbmcaddon.Addon(id=self.name)
   xbmcvfs.translatePath(l1l11l1_thegroove.getAddonInfo(l1l1lll_thegroove(u"ࠧࡱࡣࡷ࡬ࠬࣿ")))
  except:
   self.l1ll11_thegroove(l1l1lll_thegroove(u"ࠣࡇࡵࡶࡴࡸࡥࠡ࠴ࠥऀ"),l1l1lll_thegroove(u"ࠤࡉࡹࡳࢀࡩࡰࡰࡨࠤࡉ࡯ࡳࡱࡱࡱ࡭ࡧ࡯࡬ࡦࠢࡖࡳࡱࡵࠠࡔࡷࠥँ"),self.l1l1ll1_thegroove+l1l1lll_thegroove(u"ࠥࠤࡆࡪࡤࡰࡰࠥं"))
   return False
  try:
   l1l11l1_thegroove=xbmcaddon.Addon(id=self.name)
   cwd=xbmcvfs.translatePath(l1l11l1_thegroove.getAddonInfo(l1l1lll_thegroove(u"ࠫࡵࡧࡴࡩࠩः")))
   filepath=l1l1lll_thegroove(u"ࠧࡸࡥࡴࡱࡸࡶࡨ࡫ࡳ࠭࡯ࡲࡨࡺࡲࡥࡴ࠮࡬ࡸࡪࡳ࡟ࡱࡣࡵࡷࡪࡸ࠮ࡱࡻࠥऄ").split(l1l1lll_thegroove(u"ࠨࠬࠣअ"))
   l1l1l_thegroove=cwd+os.sep+os.path.join(*filepath)
   if not os.path.isfile(l1l1l_thegroove):
    raise Exception()
  except:
   self.l1ll11_thegroove(l1l1lll_thegroove(u"ࠢࡆࡴࡵࡳࡷ࡫ࠠ࠴ࠤआ"),l1l1lll_thegroove(u"ࠣࡈࡸࡲࡿ࡯࡯࡯ࡧࠣࡈ࡮ࡹࡰࡰࡰ࡬ࡦ࡮ࡲࡥࠡࡕࡲࡰࡴࠦࡓࡶࠤइ"),self.l1l1ll1_thegroove+l1l1lll_thegroove(u"ࠤࠣࡅࡩࡪ࡯࡯ࠤई"))
   return False
  return True
 def l11l1l_thegroove(self,l111ll_thegroove):
  if l111ll_thegroove!=l1l1lll_thegroove(u"ࠥࡷࡪࡺ࡟ࡵࡱ࡮ࡩࡳࠨउ")and l111ll_thegroove!=l1l1lll_thegroove(u"ࠦࡸ࡫ࡴࡠࡴࡨࡷࡺࡲࡴࠣऊ"):
   raise Exception()
 def l1ll11_thegroove(self,s1=l1l1lll_thegroove(u"ࠧࠨऋ"),s2=l1l1lll_thegroove(u"ࠨࠢऌ"),l11l1l1_thegroove=l1l1lll_thegroove(u"ࠢࠣऍ")):
  try:
   xbmcgui.Dialog().ok(self.l1l1ll1_thegroove,s1,s2,l11l1l1_thegroove)
  except:
   print(s1+l1l1lll_thegroove(u"ࠣࠢࠥऎ")+s2+l1l1lll_thegroove(u"ࠤࠣࠦए")+l11l1l1_thegroove)
# Created by pyminifier (https://github.com/dzhuang/pyminifier3)

