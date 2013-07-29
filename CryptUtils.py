#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Crypto.Cipher import AES
import base64
from config import AESkey


_BS_ = AES.block_size
_pad_ = lambda s: s + (_BS_ - len(s) % _BS_) * chr(_BS_ - len(s) % _BS_)
_unpad_ = lambda s: s[0:-ord(s[-1])]


class Crypt(object):

    def __init__(self, key=""):
        self._key = key

    def __buildCipher(self, key):
        if key == None:
            key = self._key
        return AES.new(key)

    def decode(self, data, key=None):
        try:
            cipher = self.__buildCipher(key)
            return _unpad_(cipher.decrypt(data))
        except:
            return data

    def encode(self, data, key=None):
        cipher = self.__buildCipher(key)
        return cipher.encrypt(_pad_(data))

    def decode64(self, data, key=None):
        dt = base64.b64decode(data)
        return self.decode(dt, key)

    def encode64(self, data, key=None):
        dt = self.encode(data, key)
        return base64.b64encode(dt)

    def getCryptUrl(self, string):
        if string.find("?") < 0:
            string += "?"
        if not string.endswith("?"):
            string += "&"
        string += "cyt=1"
        return string

    def setKey(self, key):
        self.key = key

crypt = Crypt(AESkey)
