#!/usr/bin/env python
# -*- coding: utf-8 -*-

from libMA import *
from config import deviceToken, loginId, password


device = Device(token=deviceToken)
user = device.newUser(loginId=loginId, password=password)
loginData = user.login()
areaList = user.exploration.getAreaList()
areaList = areaList.response.body.exploration_area.area_info_list.area_info
targetAreaId = None
for area in areaList:
    if int(area.prog_area) < 100:
        targetAreaId = area.id
        break
floorList = user.exploration.getFloorList(targetAreaId)
floorList = floorList.response.body.exploration_floor.floor_info_list.floor_info
if isinstance(floorList,dict):
    floorList = [floorList]
targetFloorId = None
for floor in floorList:
    if int(floor.progress) < 100:
        targetFloorId = floor.id
        break

floorCost = int(floor.cost)
exploreData = user.exploration.getFloorStatus(targetAreaId, targetFloorId)
leftAP = exploreData.response.header.your_data.ap.current
while int(leftAP) > floorCost:
    print "now left %s AP" % leftAP
    exploreData = user.exploration.explore(targetAreaId, targetFloorId)
    explore = exploreData.response.body.explore
    print "get exp:%s,gold:%s" % (explore.get_exp, explore.gold)
    leftAP = exploreData.response.header.your_data.ap.current
