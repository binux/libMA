#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-15 18:37:38

import os
import re
import uuid
import time
import hashlib
import _winreg
import win32api
import win32gui
import win32con
import requests
import win32com.client
from ctypes import windll

import config

INVITE = '40e3f'

def change_guid(guid=None):
    if not guid:
        guid = str(uuid.uuid4())
    key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\BlueStacks\Guests\Android',0, _winreg.KEY_ALL_ACCESS)
    value, vtype = _winreg.QueryValueEx(key, 'BootParameters')
    new_value = re.sub('GUID=[\w-]+', 'GUID=%s' % guid, value)
    _winreg.SetValueEx(key, 'BootParameters', 0, 1, new_value)

def restart_bluestacks():
    os.system(r'"C:\Program Files\BlueStacks\HD-Quit.exe"')
    time.sleep(3)
    os.system(r'"C:\Program Files\BlueStacks\HD-StartLauncher.exe"')

def click(x, y):
    hwnd = win32gui.GetForegroundWindow()
    x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)
    x, y = x1+x, y1+y
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

def send(text):
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys(text)

def get_color(x, y):
    hwnd = win32gui.GetForegroundWindow()
    x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)
    x, y = x1+x, y1+y
    return windll.gdi32.GetPixel(windll.user32.GetDC(0), x, y)

def find_window(title):
    hwnd = win32gui.FindWindow(None, title)
    assert hwnd
    win32gui.SetForegroundWindow(hwnd)
    return win32gui.GetWindowRect(hwnd)

USERNAME=""
PASSWORD=config.password
PROJECT_ID=125
def get_tel_f02():
    ret = requests.get("http://f02.cn/httpUserGetMobileAction.do?userID=%s&password=%s&size=1&projectID=%s" % (USERNAME, PASSWORD, PROJECT_ID))
    lines = ret.text.splitlines()
    assert lines[0].strip() == '111', ret.text
    return lines[1].strip()

def get_sms_f02(mobile):
    ret = requests.get("http://f02.cn/httpGetCodeAction.do?userID=%s&password=%s&projectID=%s&mobile=%s" % (USERNAME, PASSWORD, PROJECT_ID, mobile))
    lines = ret.text.splitlines()
    assert lines[0].strip() == '111', ret.text
    assert lines[1].split(';')[0] == mobile, ret.text
    return lines[1].split(';')[1].strip()

token = None
uid = ''
pwd = ''
pid = 292
def get_tel_fq():
    global tel
    global token
    if not token:
        ret = requests.post("http://sms.xudan123.com/do.aspx", {
            'action': 'loginIn',
            'uid': uid,
            'pwd': pwd,
            })
        token = ret.text.split('|')[1].strip()
    ret = requests.post("http://sms.xudan123.com/do.aspx", {
        'action': 'getMobilenum',
        'pid': 292,
        'uid': uid,
        'token': token,
        })
    assert ret.text != 'no_data', ret.text
    tel = ret.text.split('|')[0].strip()
    assert tel.isdigit()
    return tel

def get_sms_fq(mobile):
    global code
    ret = requests.post("http://sms.xudan123.com/do.aspx", {
        'action': 'getVcodeAndReleaseMobile',
        'mobile': mobile,
        'uid': uid,
        'token': token,
        'author_uid': 'binux',
        })
    assert ret.text != 'no_data', ret.text
    assert len(ret.text.split('|')) > 1, ret.text
    m = re.search('\d+', ret.text.split('|')[1])
    assert m, ret.text
    code = m.group(0)
    return code

tasoo = requests.Session()
def get_tel_tasoo():
    global tasoo
    global mobile
    ret = tasoo.post('http://www.tasoo.net/Handle/AjaxHandle.ashx?Type=Login', {
        'uid': config.tasoo_uid,
        'pwd': config.tasoo_pwd,
        })
    tasoo.cookies = ret.cookies
    ret = tasoo.post('http://www.tasoo.net/Handle/CodeHandle.ashx?Type=GetPhone', {
        'Phone': '',
        'CategoryFlag': '0083',
        'hold': 0,
        })
    assert '|' in ret.text, ret.text
    mobile = ret.text.split('|')[0]
    return mobile

def get_sms_tasoo(mobile):
    global tasoo
    global code
    ret = tasoo.post('http://www.tasoo.net/Handle/CodeHandle.ashx?Type=GetCode', {
        'Phone': mobile,
        'CategoryFlag': '0083',
        'SuperiorID': '17958',
        })
    assert ret.text != 'not_msg', ret.text
    m = re.search('\d{6}', ret.text)
    assert m, ret.text
    code = m.group(0)
    return code

def test():
    while True:
        hwnd = win32gui.GetForegroundWindow()
        x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)
        x, y = win32api.GetCursorPos()
        print "(%s, %s, %s, None)," % (x-x1, y-y1, get_color(x, y))
        time.sleep(1)

def color_like(a, b):
    r = abs((a >> 16 & 0xff)-(b >> 16 & 0xff))
    g = abs((a >> 8 & 0xff)-(b >> 8 & 0xff))
    b = abs((a & 0xff)-(b & 0xff))
    return r+g+b

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        test()

    get_tel, get_sms = get_tel_tasoo, get_sms_tasoo
    #get_tel, get_sms = get_tel_fq, get_sms_fq
    #get_tel, get_sms = get_tel_f02, get_sms_f02

    #get_tel()
    change_guid()
    restart_bluestacks()
    time.sleep(5)
    find_window('BlueStacks App Player for Windows (beta-1)')
    #test()
    #change_guid()
    #restart_bluestacks()

    def enter_tel():
        global tel
        print "getting telnum:",
        while True:
            try:
                tel = get_tel()
                #tel = '12345678901'
                print tel
                return tel
            except AssertionError, e:
                print e
                time.sleep(2)
                continue

    def enter_code():
        global tel
        global code
        print "getting check code:",
        time.sleep(10)
        while True:
            try:
                code = get_sms(tel)
                #code = '123467'
                print code
                return code
            except AssertionError, e:
                print e
                time.sleep(2)

    steps = [
        (161, 136, 14341842, None),   # bluestacks start
        (131, 183, 0, lambda: time.sleep(10)),    # click all apps
        (708, 267, 16513786, None),   # start ma
        (627, 416, 1315992, None),    # regist
        (595, 412, 9452032, None),    # choose server
        (522, 133, 16119028, enter_tel),   # tel
        (626, 208, 2006039, None),
        (618, 355, 16119028, enter_code),   # check code
        (641, 441, 1447578, lambda: time.sleep(3)),    # next step
        (727, 257, 16119028, PASSWORD),   # password2
        (732, 165, 16119028, PASSWORD),   # password1
        (745, 351, 16119028, INVITE),     # invite
        (571, 444, 0, lambda: time.sleep(2)),   #go
        (560, 514, 0, None),  # go
        ]
    for i, (x, y, color, text) in enumerate(steps):
        print 'step %d' % i
        if color:
            while color_like(get_color(x, y), color) > 10:
                time.sleep(1)
        click(x, y)
        if text:
            if callable(text):
                text = text()
            if text:
                time.sleep(1)
                send(text)
        time.sleep(1)
    # over
    while get_color(619, 601) == 0:
        click(619, 601)
        time.sleep(1)

    from ma import MA
    print tel, code
    ma = MA()
    ma.login(tel, PASSWORD)
    ma.save_character(tel)

    ma.tutorial_next(7030)
    ma.tutorial_next(8000)
    os.system(r'"C:\Program Files\BlueStacks\HD-Quit.exe"')
