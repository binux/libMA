#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-31 19:36:06

import ma
import time
import random
import datetime
import gevent
import gevent.pywsgi
from webob import Request
from db import accountdb, battledb
from levelup_bot import LevelBot
from lxml.etree import XMLSyntaxError
import gevent.monkey; gevent.monkey.patch_all()

TARGET_LV = 25

class WebLevelBot(LevelBot):
    master_cards = {}   # shared master cards
    def login(self, *args, **kwargs):
        super(WebLevelBot, self).login(*args, **kwargs)
        if not self.__class__.master_cards:
            self.__class__.master_cards = self.ma.master_cards
        else:
            self.ma.master_cards = self.__class__.master_cards

    def _print(self, message):
        print self.login_id, message
        with open('/tmp/libma.%s.log' % self.login_id, 'a') as fp:
            fp.write('%s ' % datetime.datetime.now())
            fp.write(message.encode('utf8') if isinstance(message, unicode) else message)
            fp.write('\n')

def _run_task(account):
    bot = WebLevelBot()
    bot.login(account['id'], account['pwd'])
    account['name'] = bot.ma.name
    account['uid'] = int(bot.ma.user_id)
    account['lv'] = bot.ma.level
    account['friends'] = bot.ma.friends
    account['friend_max'] = bot.ma.friend_max
    accountdb.update(**account)
    bot._print("%s-%s(%s%%): AP:%s/%s BC:%s/%s Gold:%s Cards:%s %s" % (
                bot.ma.name, bot.ma.level, bot.ma.percentage,
                bot.ma.ap, bot.ma.ap_max, bot.ma.bc, bot.ma.bc_max,
                bot.ma.gold, len(bot.ma.cards),
                "Free Point:%s " % bot.ma.free_ap_bc_point if bot.ma.free_ap_bc_point else '',
                ))

    bot.task_check()
    if account['status'] == 'DONE':
        return True
    friends = accountdb.find_friends()
    for i in range(bot.ma.friend_max - bot.ma.friends):
        try:
            cur = friends.next()
            if int(cur['uid']) == int(bot.ma.user_id):
                cur = friends.next()
            bot.ma.add_friend(cur['uid'])
        except StopIteration:
            break
    if not bot.build_roundtable('battle'):
        bot._print('build battle roundtalbe failed!')
        return True
    offset = random.randint(0, 500)
    while bot.ma.bc >= bot.ma.cost:
        try:
            battle = False
            battle_list = []
            for cur in battledb.scan(offset):
                offset += 1
                if int(cur['uid']) % 2 != account['rounds'] % 2:
                    continue
                if (bot.ma.roundtable[0].hp/cur['atk']*1.2+1)*bot.ma.roundtable[0].power < cur['hp']:
                    continue
                battle_list.append(cur)
                if len(battle_list) > 50:
                    break
            if not battle_list:
                break
            random.shuffle(battle_list)
            battle = True
            for cur in battle_list:
                try:
                    hp, atk = bot.battle(cur['uid'])
                    if hp != cur['hp'] or atk != cur['atk']:
                        battledb.update(cur['uid'], hp, atk)
                except ma.HeaderError, e:
                    if e.code == 8000:
                        bot._print('changing battle list(offset:%s): %s' % (offset, e.message))
                        break
                    raise
            if not battle or bot.ma.bc < bot.ma.cost:
                bot.task_no_bc_action()
            if not battle:
                break
            account['lv'] = bot.ma.level
            account['status'] = 'RUNNING'
            accountdb.update(**account)
        except XMLSyntaxError, e:
            bot._print('xml error')
            continue

    account['lv'] = bot.ma.level
    account['friends'] = bot.ma.friends
    account['friend_max'] = bot.ma.friend_max
    if bot.ma.level >= account['target_lv']:
        account['status'] = 'DONE'
        accountdb.update(**account)
    return True

def run_task(account):
    account = dict(account)
    try:
        print 'running account:', account['id']
        account['status'] = 'RUNNING'
        accountdb.update(**account)
        _run_task(account)
        account['nextime'] = time.time() + 60*60
    except ma.HeaderError, e:
        print account['id'], 'FAILED', e
        if e.code == 1000:
            account['status'] = 'FAILED'
            accountdb.update(**account)
            return False
        elif e.code == 8000:
            import traceback; traceback.print_exc()
        account['nextime'] = time.time() + 10*60
    except Exception, e:
        import traceback; traceback.print_exc()
        account['nextime'] = time.time() + 5*60
    except XMLSyntaxError, e:
        account['nextime'] = time.time() + 3*60
    finally:
        if account['status'] not in ('FAILED', 'DONE'):
            account['rounds'] += 1
            account['status'] = 'PENDING'
            accountdb.update(**account)
    print 'finished account:', account['id']

def auto_start():
    while True:
        now = time.time()
        for each in accountdb.scan('PENDING'):
            if each['nextime'] <= now:
                gevent.spawn(run_task, each)
        time.sleep(30)

def web_app(environ, start_response):
    request = Request(environ)
    if request.path == '/':
        template = ('<html><body>'
                    '<form action="/add">add <input name="id" /><input name="pwd" /> '
                    'group:<input name=group /><input type=submit /></form>'
                    '<pre>%s</pre></body></html>')
        content = []
        content.append('<h1>RUNNING</h1><hr />')
        for cur in accountdb.scan('RUNNING'):
            cur['mintime'] = datetime.datetime.fromtimestamp(cur['intime'])
            cur['mnextime'] = cur['nextime'] and datetime.datetime.fromtimestamp(cur['nextime'])
            content.append('%(mintime)s <a href="/log?id=%(id)s">%(id)s</a>:%(invite)s %(name)s lv:%(lv)s rounds:%(rounds)s' % cur)
        content.append('<h1>PENDING</h1><hr />')
        for cur in accountdb.scan('PENDING'):
            cur['mintime'] = datetime.datetime.fromtimestamp(cur['intime'])
            cur['mnextime'] = cur['nextime'] and datetime.datetime.fromtimestamp(cur['nextime'])
            content.append('%(mintime)s <a href="/log?id=%(id)s">%(id)s</a>:%(invite)s %(name)s lv:%(lv)s rounds:%(rounds)s '
                           '%(mnextime)s <a href="/run?id=%(id)s&done=0">run</a>' % cur)
        content.append('<h1>DONE</h1><hr />')
        done = []
        for cur in accountdb.scan('DONE'):
            cur['mintime'] = datetime.datetime.fromtimestamp(cur['intime'])
            cur['mnextime'] = cur['nextime'] and datetime.datetime.fromtimestamp(cur['nextime'])
            done.append('%(mintime)s <a href="/log?id=%(id)s">%(id)s</a>:%(invite)s' % cur)
        content.append(' '.join(done))
        content.append('<h1>FAILED</h1><hr />')
        for cur in accountdb.scan('FAILED'):
            cur['mintime'] = datetime.datetime.fromtimestamp(cur['intime'])
            cur['mnextime'] = cur['nextime'] and datetime.datetime.fromtimestamp(cur['nextime'])
            content.append('%(mintime)s <a href="/log?id=%(id)s">%(id)s</a>:%(invite)s %(name)s lv:%(lv)s rounds:%(rounds)s '
                           '<a href="/run?id=%(id)s&done=0">run</a>' % cur)
        # return 
        start_response("200 OK", [("Content-Type", "text/html")])
        return template % '\n'.join(content)
    elif request.path == '/add':
        _id = request.GET['id']
        pwd = request.GET['pwd']
        group = request.GET['group']
        accountdb.add(_id, pwd, group=group)
        start_response("302 FOUND", [("Location", "/")])
        return 'redirect'
    elif request.path == '/run':
        _id = int(request.GET['id'])
        done = int(request.GET.get('done', 1))
        if done == 0:
            data = accountdb.get(_id)
            if not data:
                start_response("302 FOUND", [("Location", "/run?id=%s&done=2" % _id)])
                return 'redirect'
            gevent.spawn(run_task, data)
            start_response("302 FOUND", [("Location", "/run?id=%s&done=1" % _id)])
            return 'redirect'
        elif done == 2:
            start_response("200 OK", [("Content-Type", "text/html")])
            return 'id:%s failed!' % _id
        else:
            start_response("302 FOUND", [("Location", "/")])
            return 'redirect'
    elif request.path == '/log':
        _id = request.GET['id']
        try:
            with open('/tmp/libma.%s.log' % _id, 'r') as fp:
                start_response("200 OK", [("Content-Type", "text/plain")])
                return fp.readlines()
        except IOError, e:
            start_response("404 NOT FOUND", [])
            return '404'
    else:
        start_response("404 NOT FOUND", [])
        return '404'

if __name__ == '__main__':
    server = gevent.pywsgi.WSGIServer(("", 8888), web_app)
    gevent.spawn(auto_start)
    server.serve_forever()
