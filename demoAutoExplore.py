#!/usr/bin/env python
# -*- coding: utf-8 -*-

from libMA import *
from config import deviceToken, loginId, password


device = Device(token=deviceToken)
user = device.newUser(loginId=loginId, password=password)
loginData = user.login()
arealist = user.getAreaList()
area = arealist.find(lambda x:int(x.progress[0])<100)
floorlist = area.getFloorList()
floor = floorlist.find(lambda x:int(x.progress[0])<100)
print "now ap is %s/%s"%(str(user.ap[0]),str(user.ap[1]))
while int(user.ap[0])>40:
    exploreData = floor.explore()
    print "get exp:%s,gold:%s"%(exploreData.explore.get_exp,
                                exploreData.explore.gold)
    print "left ap %s/%s"%(str(user.ap[0]),str(user.ap[1]))
