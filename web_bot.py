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
    master_cards = {}   # shared master cards
    card_rev = None
    atk_log = {}   # shared atk log
    connected = 0
    def __init__(self, ws):
        self.ws = ws
        self.offline = False
        self.__class__.connected += 1
        Bot.__init__(self)
        self.atk_log = self.__class__.atk_log

    def login(self, login_id, password):
        self.ma.login(login_id, password)
        self._print("by binux@ma.binux.me")
        assert self.ma.islogin, 'login error!'
        self.ma.mainmenu()
        if not self.__class__.master_cards or self.__class__.card_rev != self.ma.revision['card_rev']:
            self.ma.masterdata_card()
            self.__class__.master_cards.clear()
            self.__class__.master_cards.update(self.ma.master_cards)
            self.__class__.card_rev = self.ma._card_rev
            self.ma.master_cards = self.__class__.master_cards
        else:
            self.ma.master_cards = self.__class__.master_cards
        self.ma.roundtable_edit()

    def __del__(self):
        self.__class__.connected -= 1
        print "conn-1=%d" % self.connected

    def _print(self, message):
        if self.ws:
            self.ws.send(message)

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
        if not offline:
            ws.send("offline disallowed.")

        if login_id+password in offline_bots:
            ws.send("bot reconnected!")
            bot = offline_bots[login_id+password]
            bot.ws = ws
            bot.offline = offline
            while not ws.closed:
                time.sleep(60)
            return

        bot = WebSocketBot(ws)
        if offline:
            bot.offline = True
            offline_bots[login_id+password] = bot

        print "conn+%s=%d %s" % (environ.get('HTTP_X_REAL_IP', environ['REMOTE_ADDR']),
                                 WebSocketBot.connected, environ.get('HTTP_USER_AGENT', '-'))
        while True:
            try:
                bot.run(login_id, password, int(area) if area else None)
            except ma.HeaderError, e:
                print e.code, e.message
                if bot.ws:
                    bot.ws.send('%s %s %s' % (e.code, e.message, 'sleep for 10min'))
                time.sleep(10*60)
                continue
            except (socket.error, WebSocketError), e:
                if bot.offline:
                    bot.ws = None
                    continue
                break
            except Exception, e:
                import traceback; traceback.print_exc()
                try:
                    bot.ws.send('%s' % e)
                except WebSocketError:
                    break
                break
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
