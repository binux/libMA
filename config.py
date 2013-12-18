#!/usr/bin/env python
# -*- coding: utf-8 -*-

# debug mode
DEBUG = False
PRINT = False

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
USER_AGENT = "Million/102 (aries; aries; 4.1.1) Xiaomi/aries/aries:4.1.1/JRO03L/3.12.13:user/release-keys"

# AESkey,god knows where it from
AESkey = "011218525486l6u1"

RSAkey = """MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAM5U06JAbYWdRBrnMdE2bEuDmWgUav7xNKm7i8s1Uy/\nfvpvfxLeoWowLGIBKz0kDLIvhuLV8Lv4XV0+aXdl2j4kCAwEAAQ==""".decode("base64")

#PUSH SERVER need this key
DES_KEY = "Fwe3;$84@kl3221554*G(|d@"

tasoo_uid = None
tasoo_pwd = None

try:
    from local_config import *
except ImportError:
    pass
