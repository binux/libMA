#!/usr/bin/env python
# -*- coding: utf-8 -*-

from HttpUtils import App, buildOpener


class Device(object):

    def __init__(self, token):
        self.token = token
        self.app = App()

    def check_inspection(self):
        data = self.app.check__inspection()
        return data

    def notification_postDevicetoken(self, loginId, password,
                                     token=None, S="nosessionid"):
        if token == None:
            token = self.token
        params = {
            "S": S,  # magic,don't touch
            "login_id": loginId,
            "password": password,
            "token": token.encode("base64")
        }
        data = self.app.notification_post__devicetoken(params)
        return data

    def newUser(self, loginId, password):
        # self.notification_postDevicetoken(loginId, password)
        return User(self.app, loginId, password)


class User(object):

    def __init__(self, app, loginId, password):
        self.login_id = loginId
        self.password = password
        self.app = app
        self.session = None
        self.userId = None
        self.menu = Menu(self.app)
        self.exploration = Exploration(self.app)

    def login(self):
        params = {
            "login_id": self.login_id,
            "password": self.password,
        }
        data = self.app.login(params)
        self.session = data.response.header.session_id
        self.userId = data.response.body.login.user_id
        self.cardList = data.response.header.your_data.owner_card_list.user_card
        return data

    def mainmenu(self):
        data = self.app.mainmenu()
        return data


class Menu(object):

    def __init__(self, app):
        self.app = app

    def menulist(self):
        data = data = self.app.menu_menulist()
        return data

    def fairyselect(self):
        data = data = self.app.menu_fairyselect()
        return data


class Exploration(object):

    def __init__(self, app):
        self.app = app

    def getAreaList(self):
        data = self.app.exploration_area()
        return data

    def getFloorList(self, areaId):
        params = {
            "area_id": areaId,
        }
        data = self.app.exploration_floor(params)
        return data

    def getFloorStatus(self, areaID, floorId, check="1"):
        params = {
            "area_id": areaID,
            "floor_id": floorId,
            "check": check,  # magic,don't touch
        }
        data = self.app.exploration_get__floor(params)
        return data

    def explore(self, areaId, floorId, autoBuild="1"):
        params = {
            "area_id": areaId,
            "floor_id": floorId,
            "auto_build": autoBuild,
        }
        data = self.app.exploration_explore(params)
        return data

    def fairyFloor(self, serialId, userId, check="1"):
        params = {
            "serial_id": serialId,
            "user_id": userId,
            "check": check,  # magic,don't touch
        }
        data = self.app.exploration_fairy__floor(params)
        return data

    def fairybattle(self, serialId, userId):
        params = {
            "serial_id": serialId,
            "user_id": userId,
        }
        data = self.app.exploration_fairybattle(params)
        return data

    def fairyhistory(self, serialId, userId):
        params = {
            "serial_id": serialId,
            "user_id": userId,
        }
        data = self.app.exploration_fairyhistory(params)
        return data

    def fairyLose(self, serialId, userId):
        params = {
            "serial_id": serialId,
            "user_id": userId,
        }
        data = self.app.exploration_fairy__lose(params)
        return data

    def fairyWin(self, serialId, userId):
        params = {
            "serial_id": serialId,
            "user_id": userId,
        }
        data = self.app.exploration_fairy__win(params)
        return data

if __name__ == "__main__":
    from config import deviceToken, loginId, password
    device = Device(token=deviceToken)
    user = device.newUser(loginId=loginId, password=password)
    loginData = user.login()
