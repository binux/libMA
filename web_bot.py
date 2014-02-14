#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-25 17:10:07

import os
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

def wrapper(self, cls, func):
    def wrap(*args, **kwargs):
        _ = func(*args, **kwargs)
        cls._card_rev = self.ma._card_rev
        return _
    return wrap

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
        self.ma._master_cards = cls._master_cards
        self.ma.masterdata_card = wrapper(self, cls, self.ma.masterdata_card)
        _ = self.ma.master_cards
        self.ma.roundtable_edit()

    def run(self, login_id, password, area=None):
        while not self._quit:
            try:
                self._print('running...')
                super(WebSocketBot, self).run(login_id, password, int(area) if area else None)
            except ma.HeaderError, e:
                print e.code, e.message
                self._print('%s %s %s' % (e.code, e.message, 'sleep for 10min'))
                if e.code == 1000:
                    break
                time.sleep(10*60)
                if self.offline:
                    continue
                if self.ws:
                    continue
                break
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

    def quit(self):
        # fix references
        self.ma.masterdata_card = None
        self._quit = True

    def on_wsmessage(self, message):
        print message

        cmd, rest = message.split(' ', 1)
        if cmd == 'item_use':
            self.ma.item_use(int(rest))
            self.report()
        if cmd == 'report':
            self.report()
        elif cmd == 'set':
            attr, value = rest.split(' ', 1)
            setattr(self, attr, int(value))
        elif cmd == 'set_bool':
            attr, value = rest.split(' ', 1)
            setattr(self, attr, value == 'true')
        elif cmd == 'roundtable':
            _type, value = rest.split(' ', 1)
            self.roundtable[_type] = value
        elif cmd == 'sort_card':
            by, _filter = rest.split(' ', 1)
            for card in self.sort_card(by):
                if _filter == 'true' and (card.lv == 1 or card.lv == card.lv_max):
                    continue
                string = u"%s %s-%d lv%d/%d %s=%s" % (card.serial_id, card.name, card.rarity, card.lv, card.lv_max,
                                           by, getattr(card, by))
                self._print(string)
        elif cmd == 'fairy_rewards':
            self.fairy_rewards()
            if self.SELL_CARDS:
                self.sell_cards(self.SELL_CARDS)
            self.report()
        elif cmd == 'compound':
            base_card, target_lv, max_lv = map(int, rest.split(' '))
            base_card = self.ma.cards[base_card]
            self.compound(base_card, target_lv, max_lv)
        elif cmd == 'merge':
            min_lv = int(rest)
            self.merge(min_lv)
        else:
            self._print('unknow command: %s' % message)
            return
        self._print(message)

    def on_wsclose(self):
        #self.ws = None
        #if not self.offline:
            #self._quit = True
        pass

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
            if not message:
                bot.on_wsclose()
                break
        except (socket.error, WebSocketError), e:
            bot.on_wsclose()
            break
        except gevent.GreenletExit:
            break

        try:
            bot.on_wsmessage(message)
        except Exception, e:
            bot._print('%s' % e)

#from ma import MA, Card
#def dump_garbage():
    #print "GARBAGE:"
    #gc.collect()
    #print "GARBAGE OBJECTS:"
    #for x in gc.garbage:
        #for x in gc.garbage:
            #if not isinstance(x, MA) and not isinstance(x, Card):
                #continue
            #s = str(x)
            #print type(x), "\n ", s

offline_bots = {}
def websocket_app(environ, start_response):
    request = Request(environ)
    if request.path == '/bot' and 'wsgi.websocket' in environ:
        ws = environ["wsgi.websocket"]
        login_id = request.GET['id']
        password = request.GET['password']
        area = request.GET.get('area', None)
        server = request.GET.get('server', config.BASE_URL)
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
        bot.ma.BASE_URL = server
        bot.run(login_id, password, int(area) if area else None)
        g.kill(block=False)
        bot.quit()

        if login_id+password in offline_bots:
            print "offline bot exit. login_id=%s" % login_id
            del offline_bots[login_id+password]

    elif request.path == '/':
        start_response("200 OK", [("Content-Type", "text/html")])
        return [open(os.path.join(os.path.dirname(__file__), "bot.html")).read().replace("$CONN", str(WebSocketBot.connected)), ]
    else:
        start_response("404 NOT FOUND", [("Content-Type", "text/html")])
        return ("404 NOT FOUND", )

if __name__ == '__main__':
    #import gc
    #gc.enable()
    #gc.set_debug(gc.DEBUG_LEAK)
    gevent.monkey.patch_all()
    server = gevent.pywsgi.WSGIServer(("", 8000), websocket_app, handler_class=WebSocketHandler)
    server.serve_forever()
