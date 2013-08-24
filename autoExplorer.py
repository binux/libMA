#!/usr/bin/env python
# -*- coding: utf-8 -*-

from libMA import *
from config import deviceToken, loginId, password
from XML2Object import UUObject
import time
import logging
import urllib2
logging.basicConfig(
    #filename='/tmp/MAautoExplorer.log', filemode='a+',
    level=logging.DEBUG,
    format = '%(asctime)-15s#%(message)s'
)
firstArea = ["50002","50004"]


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
            if ftimecount >=0 and int(user.bc[0]) >= 2:
                newFairyList = []
                fairyList = user.getFairyList()
                for fairy in fairyList:
                    if fairy.isalive():
                        if fairy.fairyid in oldFairyList or fairy.isattacked():
                            newFairyList.append(fairy.fairyid)
                            logging.debug("let go %s(%s) found by %s(%s)"%(
                                fairy.fairyname, fairy.fairyid,
                                fairy.playername, fairy.playerid))
                            break
                        else:
                            logging.debug("attack %s(%s) found by %s(%s)"%(
                                fairy.fairyname, fairy.fairyid,
                                fairy.playername, fairy.playerid))
                            fairy.attack()
                            logging.debug("bc left %s/%s"%(
                                str(user.bc[0]), str(user.bc[1])))
                oldFairyList = newFairyList
            else:
                ftimecount += 1
            time.sleep(1)
        except urllib2.HTTPError, exception:
            if exception.code == 500:
                logging.debug("http 500 happend, wait for 1min")
                ftimecount -= 1
            else:
                logging.exception("unexcept http error happend")
        except:
            logging.exception("something go wrong,trying to relogin after 5min")
            timecount += 1
            time.sleep(10)
            loginData = user.login()
        
        try:
            if timecount >= 10:
                timecount = 0
                areaList = user.getAreaList()
                area = areaList.find(lambda x:x.areaid in firstArea)
                if not area:
                    area = areaList.find(lambda x:x.areaid.startswith("5"))
                if not area:
                    area = areaList.find(lambda x:len(x.areaid)>3 and
                                         int(x.progress[0])<100)
                if not area:
                    area = areaList.find(lambda x:int(x.progress[0])<100)
                if area:
                    floorList = area.getFloorList()
                    floor = floorList.find(lambda x:int(x.progress[0])<100)
                    if not floor:
                        floor = floorList[0]
                    while floor and int(user.ap[0])>=floor.cost:
                        print floor.floorid, user.ap, floor.cost
                        logging.debug("explore %s(%s):floor(%s) progress:%s"%(
                            area.areaname, area.areaid,
                            floor.floorid, int(floor.progress[0])))
                        exploreData = floor.explore()
                        logging.debug("get exp:%s,gold:%s"%(
                            exploreData.explore.get_exp,
                            exploreData.explore.gold))
                        logging.debug("left ap %s/%s"%(
                            str(user.ap[0]),str(user.ap[1])))
        except urllib2.HTTPError, exception:
            if exception.code == 500:
                logging.debug("http 500 happend, wait for 1min")
                timecount -= 1
            else:
                logging.exception("unexcept http error happend")
        except:
            logging.exception("something go wrong,trying to relogin after 5min")
            timecount += 1
            time.sleep(1)
            loginData = user.login()
        time.sleep(1)
        timecount +=1
    except:
        pass
