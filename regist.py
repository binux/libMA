#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-09-07 10:44:56

import re
import time
import config
import hashlib
import requests
from smsVerify import smsVerify
from ma import MA

class Tasoo:
    def __init__(self, uid, pwd):
        self.mobile = None
        self.session = requests.Session()
        self.uid = uid
        self.pwd = pwd
        self.session.post('http://www.tasoo.net/Handle/AjaxHandle.ashx?Type=Login', {
        'uid': self.uid,
        'pwd': self.pwd,
        })

    def get_tel(self):
        ret = self.session.post('http://www.tasoo.net/Handle/CodeHandle.ashx?Type=GetPhone', {
            'Phone': '',
            'CategoryFlag': '0083',
            'hold': 0,
            })
        assert '|' in ret.text, ret.text
        self.mobile = ret.text.split('|')[0]
        return self.mobile

    def get_sms(self, mobile=None):
        if mobile is None:
            mobile = self.mobile
        ret = self.session.post('http://www.tasoo.net/Handle/CodeHandle.ashx?Type=GetCode', {
            'Phone': mobile,
            'CategoryFlag': '0083',
            'SuperiorID': '17958',
            })
        assert ret.text != 'not_msg', ret.text
        m = re.search('\d{6}', ret.text)
        assert m, ret.text
        code = m.group(0)
        return code

if getattr(config, 'tasoo_uid', None):
    tasoo = Tasoo(config.tasoo_uid, config.tasoo_pwd)
def all_in_one(invitation_id):
    password = hashlib.md5(invitation_id).hexdigest()[:10]
    mobile = tasoo.get_tel()
    submit_smscode = smsVerify(mobile)
    sms = None
    time.sleep(10)
    for _ in range(10):
        try:
            sms = tasoo.get_sms(mobile)
        except AssertionError:
            time.sleep(2)
            continue
    if not sms:
        raise Exception("can't get sms")
    submit_smscode(sms)

    ma = MA()
    #ma.check_inspection()
    #ma.notification_post_devicetoken(mobile, config.password)
    ma.regist(mobile, password, invitation_id)
    ma.save_character(invitation_id+sms)
    ma.tutorial_next(7030)
    ma.tutorial_next(8000)
    return mobile, password, invitation_id+sms

if __name__ == '__main__':
    import sys
    invitation_id = sys.argv[1]
    print all_in_one(invitation_id)
