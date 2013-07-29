#!/usr/bin/env python
# -*- coding: utf-8 -*-

from libMA import *
from config import deviceToken, loginId, password


device = Device(token=deviceToken)
user = device.newUser(loginId=loginId, password=password)
loginData = user.login()
myUserId = loginData.response.body.login.user_id
# get fairy list
fairyList = user.menu.fairyselect()
fairyList = fairyList.response.body.fairy_select.fairy_event
if isinstance(fairyList,dict):
    fairyList = [fairyList]
for fairy_event in fairyList:
    if fairy_event.put_down == "1":  # still alive and not excape
        userId = fairy_event.user.id
        serialId = fairy_event.fairy.serial_id
        print "%s:%s found by %s:%s" % (fairy_event.fairy.name, serialId,
                                        fairy_event.user.name, userId)
        fairyFloor = user.exploration.fairyFloor(serialId, userId)
        # check if battled
        fairyHistory = user.exploration.fairyhistory(serialId, userId)
        attackers = fairyHistory.response.body.fairy_history.fairy.attacker_history
        flag = True
        if attackers.has_key("attacker"):
            attackers = attackers.attacker
            if isinstance(attackers,dict):
                attackers = [attackers]
            for attacker in attackers:
                print "  Listing Attackers:"
                print "   ", repr(attacker.user_id), attacker.user_name, repr(myUserId)
                if attacker.user_id == myUserId:
                    flag = False
                    break
        if flag:
            print "attack %s:%s" % (fairy_event.fairy.name, serialId)
            user.exploration.fairybattle(serialId, userId)
        else:
            print "let go %s:%s" % (fairy_event.fairy.name, serialId)
