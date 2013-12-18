#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import base64
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from config import AESkey, RSAkey


_BS_ = AES.block_size
_pad_ = lambda s: s + (_BS_ - len(s) % _BS_) * chr(_BS_ - len(s) % _BS_)
_unpad_ = lambda s: s[0:-ord(s[-1])]


class Crypt(object):
    aes_key = AESkey
    rsa_key = RSAkey
    def __init__(self, key=None):
        if key:
            self.aes_key = key
        self.aes_cipher = AES.new(self.aes_key)
        self.rsa_cipher = PKCS1_v1_5.new(RSA.importKey(self.rsa_key))

    def aes_encode(self, data, key=None):
        cipher = AES.new(key) if key else self.aes_cipher
        return cipher.encrypt(_pad_(data))

    def aes_decode(self, data, key=None):
        try:
            cipher = AES.new(key) if key else self.aes_cipher
            return _unpad_(cipher.decrypt(data))
        except:
            return data

    def rsa_encode(self, data, key=None):
        cipher = PKCS1_v1_5.new(RSA.importKey(key)) if key else self.rsa_cipher
        return cipher.encrypt(data)

    def rsa_decode(self, data, key=None):
        try:
            cipher = PKCS1_v1_5.new(RSA.importKey(key)) if key else self.rsa_cipher
            return _unpad_(cipher.decrypt(data))
        except:
            return data

    def decode64(self, data, type="AES", key=None):
        dt = base64.b64decode(data)
        if type == "AES":
            return self.aes_decode(dt, key)
        else:
            return self.rsa_decode(dt, key)

    def encode64(self, data, type="AES", key=None):
        if type == "AES":
            dt = self.aes_encode(data, key)
        else:
            dt = self.rsa_encode(data, key)
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

crypt = Crypt()

def _cryptParams(params, type="AES", key=None):
    if key is None:
        key = os.urandom(16)
    rtn = {}
    for k, v in params.items():
        if isinstance(v,unicode):
            v = v.decode("u8")
        rtn[k] = crypt.encode64(str(v), key=key)
        if type == "RSA":
            rtn[k] = crypt.encode64(rtn[k], type="RSA")
    rtn["K"] = crypt.encode64(base64.b64encode(key), type="RSA")
    return rtn
