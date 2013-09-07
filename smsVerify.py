"""
sms verify functions with demo
"""

import urllib2
import urllib
import hashlib
from Crypto.PublicKey import RSA
import binascii
import json
import string
import random
import time


def sign(strs):
    data = ("".join(strs)+"meiyumaclientserver5185f24b570b8").lower()
    return hashlib.md5(data).hexdigest().upper()

def connect(url,params = None ,headers={}):
    if not "USer-Agent" in headers:
        headers["User-Agent"] = "Apache-HttpClient/UNAVAILABLE (java 1.4)"
    if params:
        request = urllib2.Request(url,urllib.urlencode(params),headers)
    else:
        request = urllib2.Request(url,None,headers)
    response = urllib2.urlopen(request)
    return response.read()

def rsa(s):
    key = "MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBANaXfXzDAON6GRKkk0G2FQVI/1MGjE7OEcDI8sv4EPhjhxon0a6oL//dDWuWwCSMUGfHY6xGwEvChO/LBY30Wo8CAwEAAQ=="
    cert = "-----BEGIN CERTIFICATE-----\n" + key + "\n-----END CERTIFICATE-----\n"
    publicKey = RSA.importKey(cert)
    m = publicKey.encrypt(s, None)
    return binascii.b2a_hex(m[0]).upper()

def iswhilelist(phoneNum):
    data = connect("http://api.mam.sdo.com/api.php?m=Index&a=iswhitelist&phoneid="+
                   phoneNum+"&sign="+sign([phoneNum]),None,{"APPID":1000,"CHANNEL":"M216"})
    return data

def randomstr(l):
    table = string.letters# + string.digits
    return "".join([random.choice(table) for i in range(l)])

def obtain(phoneNum):
    sign = rsa(randomstr(8))#rsa("00000000")
    sign = "D5797F184A5239BF80F9D65770E3B5E2FD2D54062D2CE8E02306697BD98705D5F84C4128088B9D0F998E578633DA9B7630FBA799E8BB082EEE0D3D73B804C0E4"
    url = "http://woa.sdo.com/woa/config/obtain.shtm?smsInterceptVersion=0"+\
    "&pubKeyVersion=1.0.1&model=ibbot&signature="+sign+\
    "&appid=991000282&areaid=1&clientversion=2.5.1&endpointos=android"
    data = connect(url)
    return data

def gen_android_id(android_id = None):
    if android_id == None:
        android_id = "".join([random.choice(string.hexdigits) for i in range(16)])
    android_id = android_id[:16]
    rtn = "A"+android_id+str(int(time.time()*1000))
    rtn += randomstr(32 - len(rtn))
    return rtn

def autologin_receive(phone,android_id):
    from woa_p import P
    encoder = P("w!o2a#r4e%g6i&n8(0)^_-==991000282")
    #msg = "WOSLAe75d9c6c6bc817db1375166498399Sx-0-991000282-1"
    url = "http://woa.sdo.com/woa/autologin/receiveVerificationSms.shtm?"
    url += "phone=" + encoder.encode(phone, 0)
    url += "&msg=" + "WOSL"+android_id+"-0-991000282-1"
    url += "&appid=991000282&areaid=1&clientversion=2.5.1&endpointos=android"
    data = connect(url)
    return data
    
def verifyClientEx(smsCode, android_id):
    key = randomstr(8)
    from woa_p import P
    encoder = P(key)
    url = "http://woa.sdo.com/woa/autologin/verifyClientEx.shtm?"
    url += "signature=" + rsa(key)
    url += "&pubKeyVersion=1.0.1&uuid=" + android_id
    url += "&smsCode=" + encoder.encode(smsCode)
    url += "&imei=&appid=991000282&areaid=1&clientversion=2.5.1&endpointos=android"
    data = connect(url)
    return data
    
def checkwoasid(smsCode,android_id,phoneNum,guid,key):
    from woa_p import P
    encoder = P(key)
    data = {
        'areaId': '1',
        'optype': 0,
        'uuid': encoder.encode(android_id+"|"+phoneNum),
        'clientVersion': '2.5.1',
        'hasSDCard': 1,
        'endpointOS': 'android',
        'smsCode': smsCode,
        'appId': '991000282',
        'guid': guid,
    }
    url = "http://api.mam.sdo.com/checkwoasid.php?"
    url += "woasid="+urllib.quote(json.dumps(data).encode("base64"))
    url += "&phoneid="+phoneNum
    data = connect(url)
    return data

def smsVerify(phoneNum,android_id = None):
    android_id = gen_android_id(android_id)
    data = json.loads(obtain(phoneNum))
    guid = data["guid"]
    key = data["key"]
    autologin_receive(phoneNum, android_id)
    def callback(smsCode):
        data = checkwoasid(smsCode,android_id,phoneNum,guid,key)
        return data
    return callback

if __name__ == "__main__":
    phoneNum = "15815933930"
    android_id = "e75d9c6c6bc817db"
    callback = smsVerify(phoneNum)
    smsCode = raw_input("please Enter smsCode:")
    print smsCode
    data = callback(smsCode)
