#!/usr/bin/env python
# -*- coding: utf-8 -*-

from libMA import *
from config import deviceToken, loginId, password
import time


from config import deviceToken, loginId, password
device = Device(token=deviceToken)
user = device.newUser(loginId=loginId, password=password)
loginData = user.login()
fairylist = user.getFairyList()
print "now bc is %s/%s"%(str(user.bc[0]),str(user.bc[1]))
for fairy in filter(lambda x:x.isalive(),fairylist):
    if not fairy.isattacked():
        fairy.attack()
        time.sleep(3)
        print "left bc %s/%s"%(str(user.bc[0]),str(user.bc[1]))
