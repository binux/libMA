#!/usr/bin/env python
# -*- coding: utf-8 -*-

# debug mode
DEBUG = False

# deviceToken should be a 32 length string,i dont't want to know where it from
deviceToken = "209504d1c903cdb5d0f4b2725b7803db728948"

# loginId,your account,to Chinese Users,it shoule be your telephone number
loginId = ""

# password
password = ""

# don't touch this,don't forget to add http://
HTTP_PROXY = ""

# for chinese users
BASE_URL = "http://game1-CBT.ma.sdo.com:10001"
ACTIVE_URL = "http://push.mam.sdo.com:8000/active.php"

# starts with Million/100
USER_AGENT = "Million/100 (ibbot; ibot; 9.9) ib/ibbot/ibbot:9.9/IMM76L/ibbot/test-keys"

# AESkey,god knows where it from
AESkey = "rBwj1MIAivVN222b"

#PUSH SERVER need this key
DES_KEY = "Fwe3;$84@kl3221554*G(|d@"

try:
    from local_config import *
except ImportError:
    pass
