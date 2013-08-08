import _libMA
import logging

def list_find(lst, func):
    for item in lst:
        if func(item):
            return item

def list_findall(lst, func):
    rtn = []
    for item in lst:
        if func(item):
            rtn.append(item)
    return rtn

class Device(object):

    def __init__(self, token):
        self.token = token

    def newUser(self, loginId, password):
        device = _libMA.Device(self.token)
        user = User(loginId, password)
        return user

class User(object):

    def __init__(self, loginId, password):
        self._app = _libMA.App()
        self._user = _libMA.User(self._app, loginId, password)
        self.user = self
        logging.debug("login when user object create")
        loginData = self._user.login()
        logging.debug("update profile")
        self._update(loginData)
        self._cache = None

    def _dataCallback(self, data):
        pass

    def login(self):
        loginData = self.user.login()
        self._update(loginData.response.header.your_data)

    def _update(self, data = None):
        if data == None:
            data = self._user.mainmenu()
        yourData = data.response.header.your_data
        self.name = yourData.name
        self.level = yourData.town_level
        self.ap = [yourData.ap.current, yourData.ap.max]
        self.bc = [yourData.bc.current, yourData.bc.max]
        self.userid = data.response.body.login.user_id
        
    def getFairyList(self):
        fairyData = self._user.menu.fairyselect()
        fairyEventList = fairyData.response.body.fairy_select.fairy_event
        fairyList = []
        for fairyEvent in fairyEventList:
            fairyList.append(Fairy(self, fairyEvent))
        return fairyList

    def getAreaList(self):
        areaData = self._user.exploration.getAreaList()
        areaInfoList = areaData.response.body.exploration_area.area_info_list.area_info
        areaList = []
        for area in areaInfoList:
            areaList.append(Area(self, area))
        return areaList

class Fairy(object):

    def __init__(self, parent, data):
        self.parent = parent
        self.user = parent.user
        self._update(data)
        self._detail = None

    def _update(self, data):
        self.id = data.fairy.serial_id
        self.name = data.fairy.name
        self.lavel = data.fairy.lv
        self.timeleft = data.fairy.time_limit
        self.status = data.put_down
        self.reward = data.reward_status
        self.userid = data.user.id
        self.username = data.user.name

    def _fetch(self):
        print self.id,self.userid
        data = self.user._user.exploration.fairyFloor(self.id, self.userid)
        self._detail = data

    def isalive(self):
        return self.status == "1"

    def isattacked(self):
        if not self._detail:
            self._fetch()
        for attacker in self._detail.response.body.fairy_floor.explore.\
            fairy.attacker_history.attacker:
            if attacker.user_id == self.user.userid:
                return True
        return False

    def attack(self):
        data = self.user._user.exploration.fairybattle(self.id, self.userid)
        return data

class Area(object):

    def __init__(self, parent, data):
        self.parent = parent
        self.user = parent.user
        self._update(data)
        

    def _update(self, data):
        self.id = data.id
        self.name = data.name
        self.progress = [int(data.prog_area), int(data.prog_item)]
        self.type = data.area_type
        self._data = data

    def getFloorList(self):
        floorData = self.user._user.exploration.getFloorList(self.id)
        floorInfoList = floorData.response.body.exploration_floor.floor_info_list.floor_info
        floorList = []
        for floor in floorInfoList:
            floorList.append(Floor(self, floor))
        return floorList

class Floor(object):

    def __init__(self, parent, data):
        self.parent = parent
        self.user = parent.user
        self._update(data)

    def _update(self, data):
        self.id = data.id
        self.type = data.type
        self.progress = data.progress
        self.itemList = map(lambda i:(i.unlock, i.type), data.found_item_list.found_item)
        self._data = data

    def explore(self):
        data = self.user._user.exploration.explore(self.parent.id, self.id)
        #return data

class Roundtable(object):

    def __init__(self, parent, data):
        self.parent = parent
        self.user = parent.user
        self.cards = []
        self._update(data)

    def update(self, data):
        self.cards = []

class Card(object):

    def __init__(self, parent, data):
        self.parent = parent
        self.user = parent.user
        self._update(data)

    def _update(self, data):
        self._data = data


if __name__ == "__main__":
    from config import deviceToken, loginId, password
    device = Device(token=deviceToken)
    user = device.newUser(loginId=loginId, password=password)
    arealist = user.getAreaList()
    area = list_find(arealist, lambda x:x.id.startswith("50"))
    floorlist = area.getFloorList()
    fairylist = user.getFairyList()
    fairy = list_find(fairylist, lambda x:x.isalive() and not x.isattacked())
    
