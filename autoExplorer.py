#!/usr/bin/env python
# -*- coding: utf-8 -*-

from _libMA import *
from config import deviceToken, loginId, password
import time
import logging
import urllib2
logging.basicConfig(
    #filename='/tmp/MAautoExplorer.log', filemode='a+',
    level=logging.DEBUG,
    format = '%(asctime)-15s#%(message)s'
)
firstArea = ["50002","50004"]

def dumpdata(data):
    import json
    import os
    fname = time.strftime("%m:%d:%H:%m:%s",time.localtime())+".dump"
    f = file(os.path.join("/tmp/",fname))
    json.dump(data,f)
    f.close()

device = Device(token=deviceToken)
user = device.newUser(loginId=loginId, password=password)
loginData = user.login()
myUserId = loginData.response.body.login.user_id
timecount=90
ftimecount = 0
oldFairyList = []

class SafeException(BaseException):
    pass

while True:
    try:
        try:
            if ftimecount<0:
                ftimecount+=1
                raise SafeException
            fairyList = user.menu.fairyselect()
            fairyList = fairyList.response.body.fairy_select.fairy_event
            newFairyList = []
            for fairy_event in fairyList:
                if fairy_event.put_down == "1":  # still alive and not excape
                    userId = fairy_event.user.id
                    serialId = fairy_event.fairy.serial_id
                    flag = False
                    if serialId not in oldFairyList:
                        logging.debug("%s:%s found by %s:%s" % (fairy_event.fairy.name, serialId,
                                                    fairy_event.user.name, userId))
                        fairyFloor = user.exploration.fairyFloor(serialId, userId)
                        # check if battled
                        fairyHistory = user.exploration.fairyhistory(serialId, userId)
                        attackers = fairyHistory.response.body.fairy_history.fairy.attacker_history
                        flag = True
                        if attackers.has_key("attacker"):
                            attackers = attackers.attacker
                            for attacker in attackers:
                                #logging.debug("  Listing Attackers(Look for itself):")
                                #logging.debug("   %s:%s"%( repr(attacker.user_id), attacker.user_name))
                                if attacker.user_id == myUserId:
                                    flag = False
                                    break
                    if flag:
                        logging.debug("attack %s:%s" % (fairy_event.fairy.name, serialId))
                        battleData = user.exploration.fairybattle(serialId, userId)
                        if int(battleData.response.header.your_data.bc.current)<2:
                            logging.debug("bc is not enough")
                            ftimecount=-12
                            raise SafeException
                    else:
                        newFairyList.append(serialId)
                        if serialId not in oldFairyList:
                            logging.debug("let go %s:%s" % (fairy_event.fairy.name, serialId))
            oldFairyList = newFairyList
        except SafeException:
            pass
        except urllib2.HTTPError, exception:
            logging.debug("http 500 happend, wait for 1min")
            if exception.code == 500:
                ftimecount -= 1
        except:
            logging.exception("Exception Logged")
            logging.debug("something go wrong,trying to relogin after 5min")
            timecount += 30
            time.sleep(300)
            loginData = user.login()
            myUserId = loginData.response.body.login.user_id
        
        try:
            if timecount < 90:
                if timecount%18 == 0:
                    logging.debug("less then 15 mins,skip explore")
                timecount += 1
                raise SafeException
            logging.debug("explore every 15min")
            timecount = 0
            areaList = user.exploration.getAreaList()
            areaList = areaList.response.body.exploration_area.area_info_list.area_info
            targetAreaId = None
            targetAreaName = None
            for area in areaList:
                if area.id in firstArea:
                    targetAreaId = area.id
                    targetAreaName = area.name
                    logging.debug("find first explore Area")
                    break
                if int(area.prog_area) < 100:# or int(area.prog_item) <100:
                    targetAreaId = area.id
                    targetAreaName = area.name
                    #logging.debug("find not 100%%x2 finish area")
                    if len(targetAreaId)>3 and not targetAreaId.startswith("5"):
                        tmpAreaId = targetAreaId
                    else:
                        break
            if len(targetAreaId)<3:
                targetAreaId = tmpAreaId
            logging.debug("target area is %s:%s"%(targetAreaName,targetAreaId))
            floorList = user.exploration.getFloorList(targetAreaId)
            floorList = floorList.response.body.exploration_floor.floor_info_list.floor_info
            targetFloorId = floorList[0].id
            for floor in floorList:
                if int(floor.progress) < 100:
                    targetFloorId = floor.id
                    break
                continue
                foundItemList = floor.found_item_list.found_item
                if reduce(lambda a,b:a or b,
                          map(lambda f:f.unlock=="0",
                              foundItemList)):
                    logging.debug("find not 100%x2 finish floor")
                    targetFloorId = floor.id
                    break
            
            floorCost = int(floor.cost)
            logging.debug("floor id:%s(%s%%)"%(targetFloorId,floor.progress))
            exploreData = user.exploration.getFloorStatus(targetAreaId, targetFloorId)
            leftAP = exploreData.response.header.your_data.ap.current
            logging.debug("now AP is %s,cost %s AP/step"%(leftAP,floorCost))
            while int(leftAP) >= floorCost:
                exploreData = user.exploration.explore(targetAreaId, targetFloorId)
                explore = exploreData.response.body.explore
                logging.debug("get exp:%s,gold:%s" % (explore.get_exp, explore.gold))
                leftAP = exploreData.response.header.your_data.ap.current
                logging.debug( "now left %s AP (%s%%)" % (leftAP,explore.progress))
                if int(explore.progress)>=100:
                    logging.debug("floor explore finished")
                    timecount = 9999
                    break
            if int(leftAP) < floorCost:
                logging.debug("no enough AP waiting for 15min")
        except SafeException:
            pass
        except urllib2.HTTPError, exception:
            logging.debug("http 500 happend, wait for 1min")
            if exception.code == 500:
                timecount -= 1
        except:
            logging.exception("Exception Logged")
            logging.debug("something go wrong,trying to relogin after 5min")
            timecount += 30
            time.sleep(300)
            loginData = user.login()
            myUserId = loginData.response.body.login.user_id
        time.sleep(10)
    except:
        logging.exception("exception in loop")
    
