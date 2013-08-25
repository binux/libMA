#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-25 17:10:07

import ma
import time
import gevent
import gevent.monkey
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from webob import Request
from bot import Bot

connected = 0
class WebSocketBot(Bot):
    def __init__(self, ws):
        self.ws = ws
        Bot.__init__(self)

    def __del__(self):
        global connected
        connected -= 1
        print "conn-1=%d" % connected

    def _print(self, message):
        self.ws.send(message)

def websocket_app(environ, start_response):
    global connected
    request = Request(environ)
    if request.path == '/bot' and 'wsgi.websocket' in environ:
        connected += 1
        print "conn+%s=%d %s" % (environ['REMOTE_ADDR'], connected, environ['HTTP_USER_AGENT'])
        ws = environ["wsgi.websocket"]
        login_id = request.GET['id']
        password = request.GET['password']
        bot = WebSocketBot(ws)
        while True:
            try:
                bot.run(login_id, password)
            except WebSocketError, e:
                connected -= 1
                print "current conn-1: %d" % connected
                break
            except ma.HeaderError, e:
                ws.send('%s %s %s' % (e.code, e.message, 'sleep for 10min'))
                time.sleep(10*60)
                continue
            except Exception, e:
                ws.send('%r %s' % (e, 'sleep for 1min'))
                time.sleep(60)
                continue
    else:
        start_response("200 OK", [("Content-Type", "text/html")])
        return open("bot.html").readlines()

if __name__ == '__main__':
    gevent.monkey.patch_all()
    server = gevent.pywsgi.WSGIServer(("", 8000), websocket_app, handler_class=WebSocketHandler)
    server.serve_forever()
