#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-25 17:10:07

import ma
import time
import socket
import gevent
import config
import traceback
import gevent.monkey
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from webob import Request
from bot import Bot

class WebSocketBot(Bot):
    AP_LIMIT = 0
    SLEEP_TIME = 60
    CHOOSE_CARD_LIMIT = 30
    NCARDS_LIMIT = [3, ]
    _master_cards = {}   # shared master cards
    _card_rev = None
    atk_log = {}   # shared atk log
    connected = 0
    def __init__(self, ws):
        super(WebSocketBot, self).__init__()
        self.ws = ws
        self.offline = False
        self.__class__.connected += 1
        self.atk_log = self.__class__.atk_log

    def login(self, login_id, password):
        self.ma.login(login_id, password)
        self._print("by binux@ma.binux.me")
        assert self.ma.islogin, 'login error!'
        self.ma.mainmenu()
        

        cls = self.__class__
        def wrapper(func):
            def wrap(*args, **kwargs):
                _ = func(*args, **kwargs)
                cls._card_rev = self.ma._card_rev
                return _
            return wrap
        self.ma._master_cards = cls._master_cards
        self.ma.masterdata_card = wrapper(self.ma.masterdata_card)

        _ = self.ma.master_cards
        self.ma.roundtable_edit()

    def run(self, login_id, password, area=None):
        while True:
            try:
                super(WebSocketBot, self).run(login_id, password, int(area) if area else None)
            except ma.HeaderError, e:
                print e.code, e.message
                self._print('%s %s %s' % (e.code, e.message, 'sleep for 10min'))
                if e.code == 1000:
                    break
                time.sleep(10*60)
                continue
            except (socket.error, WebSocketError), e:
                self.ws = None
                if self.offline:
                    continue
                break
            except Exception, e:
                traceback.print_exc()
                try:
                    self._print('%s' % e)
                except WebSocketError:
                    pass
                if self.offline:
                    continue
                break

    def on_wsmessage(self, message):
        print message
        self._print(message)

    def on_wsclose(self):
        self.ws = None

    def __del__(self):
        self.__class__.connected -= 1
        print "conn-1=%d" % self.connected

    def _print(self, message):
        if self.ws:
            self.ws.send(message)

def recv_message(ws, bot):
    while True:
        try:
            message = ws.receive()
        except (socket.error, WebSocketError), e:
            bot.on_wsclose()
            break
        except gevent.GreenletExit:
            break

        bot.on_wsmessage(message)

offline_bots = {}
def websocket_app(environ, start_response):
    request = Request(environ)
    if request.path == '/bot' and 'wsgi.websocket' in environ:
        ws = environ["wsgi.websocket"]
        login_id = request.GET['id']
        password = request.GET['password']
        area = request.GET.get('area', None)
        offline = request.GET.get('offline', False)

        if offline and login_id not in config.allow_offline:
            offline = False
            ws.send("offline disallowed.")
        if offline:
            ws.send("offline enabled.")

        if login_id+password in offline_bots:
            ws.send("bot reconnected!")
            bot = offline_bots[login_id+password]
            bot.ws = ws
            bot.offline = offline
            g = gevent.spawn(recv_message, ws, bot)
            while not ws.closed:
                time.sleep(60)
            g.kill()
            return

        bot = WebSocketBot(ws)
        if offline:
            bot.offline = True
            offline_bots[login_id+password] = bot

        print "conn+%s=%d %s" % (environ.get('HTTP_X_REAL_IP', environ['REMOTE_ADDR']),
                                 WebSocketBot.connected, environ.get('HTTP_USER_AGENT', '-'))

        g = gevent.spawn(recv_message, ws, bot)
        bot.run(login_id, password, int(area) if area else None)
        g.kill()

        if login_id+password in offline_bots:
            print "offline bot exit. login_id=%s" % login_id
            del offline_bots[login_id+password]
    else:
        start_response("200 OK", [("Content-Type", "text/html")])
        return open("bot.html").readlines()

if __name__ == '__main__':
    gevent.monkey.patch_all()
    server = gevent.pywsgi.WSGIServer(("", 8000), websocket_app, handler_class=WebSocketHandler)
    server.serve_forever()
