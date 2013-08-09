#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import urllib
from CryptUtils import crypt
from cStringIO import StringIO
import gzip
from XML2Object import XML2Object
from config import HTTP_PROXY, BASE_URL, USER_AGENT


if HTTP_PROXY:
    buildOpener = lambda: urllib2.build_opener(
        urllib2.HTTPCookieProcessor(), urllib2.ProxyHandler({'http': HTTP_PROXY}))
else:
    buildOpener = lambda: urllib2.build_opener(urllib2.HTTPCookieProcessor())
__dafault_opener__ = buildOpener()

class App(object):

    base_url = BASE_URL
    def __init__(self):
        self.opener = buildOpener()

    def __getattr__(self, name):
        url = self.base_url + "/connect/app/"
        url += name.replace("__", "#").replace("_", "/").replace("#", "_")
        def func(params = {}, opener = None):
            if opener == None:
                opener = self.opener
            return connect(url, params = params, opener = opener)
        return func

# urllib2.install_opener(opener)

def _cryptParams(params):
    rtn = {}
    for k, v in params.items():
        if isinstance(v,unicode):
            v = v.decode("u8")
        rtn[k] = crypt.encode64(str(v))
    return rtn

def connect(url, params = {}, opener = None):
    if opener == None:
        opener = __dafault_opener__
    url = crypt.getCryptUrl(url)
    headers = {
        "User-Agent":
            USER_AGENT,
        "Accept-Encoding":
            "gzip, deflate",
    }
    params = _cryptParams(params)
    request = urllib2.Request(url, urllib.urlencode(params), headers)
    response = opener.open(request)
    responsion = response.read()
    try:
        f = StringIO(responsion)
        gzipper = gzip.GzipFile(fileobj = f)
        data = gzipper.read()
    except:
        data = responsion
    try:
        rtn = crypt.decode(data)
    except:
        lines = filter(lambda s: len(s) > 0, data.split("\r\n"))
        rtn = None
        for line in lines:
            if len(d) % 16 == 0:
                try:
                    rtn = crypt.decode(d)
                    break
                except:
                    pass
    if rtn != None:
        rtn = XML2Object(rtn)
    return rtn

def connectPOST(url, opeener, params):
    pass
