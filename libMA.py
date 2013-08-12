import _libMA
from HttpUtils import connect, buildOpener
from XML2Object import XMLObject,UUObject
import logging
import config
from urlparse import urljoin

def list_find(lst, func):
    for item in lst:
        if func(item):
           return item

def list_findall(lst, func):
    return filter(func, lst)

class BaseObject(object):

    def __init__(self, parent, data=None):
        self.parent = parent
        if data:
            self._update(data)

    def _update(self, data):
        pass

    def get(self, path, params):
        data = self.parent.get(path, params)
        self.parent._update(data)
        return data

    def __setattr__(self, name, value):
        try:
            object.__getattribute__(self, name)
            if not value:
                return
        except:
            pass
        object.__setattr__(self, name, value)

    def __getattr__(self, name):
        try:
            return object.__getattribute__(self, name)
        except:
            if name.startswith("_"):
                return None
            try:
                return getattr(self.parent, name)
            except:
                return None

class Device(object):

    def __init__(self, token):
        self.token = token

    def newUser(self, loginId, password):
        device = _libMA.Device(self.token)
        user = User(loginId, password)
        return user

class User(BaseObject):

    opener = buildOpener()

    def __init__(self, loginId, password):
        self._loginId = loginId
        self._password = password
        self._logined = False

    def login(self):
        params = {
            "login_id": self._loginId,
            "password": self._password,
        }
        data = self.get("login", params)
        return data

    def _update(self, data):
        if data.error.message:
            print unicode(data.error.message)
            global errorData
            errorData = data
        yourData = data.your_data
        if yourData:
            self.name = yourData.name
            self.level = yourData.town_level
            self.ap = [yourData.ap.current, yourData.ap.max]
            self.bc = [yourData.bc.current, yourData.bc.max]
            cardList = yourData.user_card
            self._logined = True
            if cardList:
                self.cards = map(lambda x:Card(self, x), cardList)
        self.userid = data.response.body.login.user_id
        self.session = data.header.session_id

    def get(self, path, params={}):
        url = urljoin(config.BASE_URL, "/connect/app/")
        url = urljoin(url, path)
        #print url
        data = XMLObject(connect(url, params,self.opener))
        self._update(data)
        return data
        
    def getFairyList(self):
        global fairyData
        fairyData = self.get("menu/fairyselect")
        fairyEventList = fairyData.fairy_select.fairy_event
        fairyList = UUObject()
        global fairyEvent
        for fairyEvent in fairyEventList:
            fairyList.append(Fairy(self, fairyEvent))
        return fairyList

    def getAreaList(self):
        areaData = self.get("exploration/area")
        areaInfoList = areaData.area_info_list.area_info
        areaList = UUObject()
        for area in areaInfoList:
            areaList.append(Area(self, area))
        return areaList

class Fairy(BaseObject):

    def _update(self, data):
        if not self._data:
            self._data = data
            self.id = data.fairy.serial_id
            self.name = data.fairy.name
            self.lavel = data.fairy.lv
            self.timeleft = data.fairy.time_limit
            self.status = data.put_down
            self.reward = data.reward_status
            self.playerid = data.user.id
            self.playername = data.user.name

    def _fetch(self):
        if True or not self._cache:
            #print "fetch fairy detail",self.id,self.playerid
            params = {
                "serial_id": self.id,
                "user_id": self.playerid,
                "check": "1",
            }
            data = self.get("exploration/fairy_floor", params)
            self._cache = data
        return self._cache

    def isalive(self):
        return self.status == "1"

    def isattacked(self):
        data = self._fetch()
        if self.userid in data.attacker_history.attacker.user_id:
            return True
        return False
        for attacker in data.attacker_history.attacker:
            if attacker.user_id == self.userid:
                return True
        return False

    def attack(self):
        params = {
            "serial_id": self.id,
            "user_id": self.playerid,
        }
        data = self.get("exploration/fairybattle/", params)
        return data

class Area(BaseObject):
    
    def _update(self, data):
        if not self._data:
            self.areaid = data.id
            self.name = data.name
            self.progress = [data.prog_area, data.prog_item]
            self.type = data.area_type
            self.cost = data.cost
            self._data = data
    
    def getFloorList(self):
        params = {
            "area_id": self.areaid
        }
        floorData = self.get("exploration/floor", params)
        floorInfoList = floorData.floor_info_list.floor_info
        floorList = UUObject()
        for floor in floorInfoList:
            floorList.append(Floor(self, floor))
        return floorList

class Floor(BaseObject):
    
    def _update(self, data):
        if not self._data:
            self.floorid = data.id
            self.type = data.type
            data = UUObject(data)
            self.itemList = map(lambda i:(i.unlock, i.type), data.found_item)
            self.progress = [data.progress,
                             len(filter(lambda x:x[0] == "1",
                                        self.itemList))*100/len(self.itemList)]
            self._data = data

    def _detail(self):
        params = {
            "area_id": self.areaid,
            "floor_id": self.floorid,
            "auto_build": "1",
        }
        data = self.get("exploration/get_floor", params)

    def explore(self):
        params = {
            "area_id": self.areaid,
            "floor_id": self.floorid,
            "auto_build": "1",
        }
        data = self.get("exploration/explore", params)
        return data

class Roundtable(BaseObject):

    def update(self, data):
        self.cards = UUObject()
        if "response" in data:
            data = data.response.body.roundtable_edit.leader_card

class Card(BaseObject):

    def _update(self, data):
        self._data = data

if __name__ == "__main__":
    from config import deviceToken, loginId, password
    device = Device(token=deviceToken)
    user = device.newUser(loginId=loginId, password=password)
    loginData = user.login()
    arealist = user.getAreaList()
    area = arealist.find(lambda x:int(x.progress[0])<100)
    floorlist = area.getFloorList()
    floor = floorlist.find(lambda x:int(x.progress[0])<100)
    print user.ap
    floor.explore()
    print user.ap
    #fairylist = user.getFairyList()
    #fairys = list_findall(fairylist, lambda x:x.isalive() and not x.isattacked())
    #map(lambda x:x.attack(),fairys)
    
