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

stop_set = set()
running_set = set()
def _run_task(account, battle_set):
    bot = WebLevelBot()
    bot.login(account['id'], account['pwd'])
    account['name'] = bot.ma.name
    account['uid'] = int(bot.ma.user_id)
    account['lv'] = bot.ma.level
    account['friends'] = bot.ma.friends
    account['friend_max'] = bot.ma.friend_max
    accountdb.update(**account)

    bot.task_check()
    if account['status'] == 'DONE':
        return True

    bot._print("%s-%s(%s%%): AP:%s/%s BC:%s/%s Gold:%s Cards:%s %s" % (
                bot.ma.name, bot.ma.level, bot.ma.percentage,
                bot.ma.ap, bot.ma.ap_max, bot.ma.bc, bot.ma.bc_max,
                bot.ma.gold, len(bot.ma.cards),
                "Free Point:%s " % bot.ma.free_ap_bc_point if bot.ma.free_ap_bc_point else '',
                ))

    # add friend
    cur_friends = [int(x) for x in bot.ma.friendlist().xpath('//user/id/text()')]
    if bot.ma.friend_max > bot.ma.friends:
        friends = list(accountdb.find_friends())
        random.shuffle(friends)
    else:
        friends = []
    for cur in friends:
        if not int(cur['uid']):
            continue
        if int(cur['uid']) == int(bot.ma.user_id):
            continue
        if int(cur['uid']) in cur_friends:
            continue
        try:
            bot._print('add friend: %(name)s(%(uid)s)' % cur)
            bot.ma.add_friend(cur['uid'])
        except ma.HeaderError:
            bot._print('add friend error: %(name)s(%(uid)s)' % cur)
            break
        except XMLSyntaxError:
            bot._print('add friend error: %(name)s(%(uid)s)' % cur)
            break

    # battle
    if not bot.build_roundtable('battle'):
        bot._print('build battle roundtalbe failed!')
        return True
    battle_list = list(battledb.scan(where="(cast(%d/atk/1.1 as int)+1)*%d>hp" % (
        bot.ma.roundtable[0].hp, bot.ma.roundtable[0].power)))
    battle_list = [x for x in battle_list if int(x['uid']) not in battle_set]
    random.shuffle(battle_list)
    bot._print('battle: %s palyers found' % len(battle_list))

    for cur in battle_list:
        if int(account['id']) in stop_set:
            stop_set.remove(int(account['id']))
            bot._print('stoped!')
            break
        if not bot.build_roundtable('battle'):
            break

        try:
            hp, atk = bot.battle(cur['uid'])
            battle_set.add(cur['uid'])
        except ma.HeaderError, e:
            if e.code == 8000:
                battle_set.add(cur['uid'])
                bot._print(e.message)
                time.sleep(2)
                continue
            raise
        except XMLSyntaxError, e:
            bot._print('xml error')
            time.sleep(2)
            continue
        if hp != cur['hp'] or atk != cur['atk']:
            battledb.update(cur['uid'], hp, atk)

        if bot.ma.free_ap_bc_point:
            account['lv'] = bot.ma.level
            account['status'] = 'RUNNING'
            accountdb.update(**account)
            bot.free_point()
        if bot.ma.bc < bot.ma.cost:
            bot.explore()
        cost = bot.ma.cost
        while bot.ma.bc < cost:
            if not bot.story():
                break

    bot.task_no_bc_action()
    bot._print("%s-%s(%s%%): AP:%s/%s BC:%s/%s Gold:%s Cards:%s %s" % (
                bot.ma.name, bot.ma.level, bot.ma.percentage,
                bot.ma.ap, bot.ma.ap_max, bot.ma.bc, bot.ma.bc_max,
                bot.ma.gold, len(bot.ma.cards),
                "Free Point:%s " % bot.ma.free_ap_bc_point if bot.ma.free_ap_bc_point else '',
                ))

    account['lv'] = bot.ma.level
    account['friends'] = bot.ma.friends
    account['friend_max'] = bot.ma.friend_max
    if bot.ma.level >= account['target_lv']:
        account['status'] = 'DONE'
        accountdb.update(**account)
    return True

def run_task(account):
    account = dict(account)
    if int(account['id']) in running_set:
        return
    print 'running account:', account['id']
    account['rounds'] += 1
    account['status'] = 'RUNNING'
    accountdb.update(**account)
    running_set.add(int(account['id']))
    try:
        battle_set = set(map(int, account['battle'].split(','))) if account['battle'] else set()
        _run_task(account, battle_set)
        account['nextime'] = time.time() + random.randint(50*60, 60*60)
    except ma.HeaderError, e:
        print account['id'], 'FAILED', e
        if e.code == 1000:
            account['status'] = 'FAILED'
            accountdb.update(**account)
            return False
        elif e.code == 8000:
            import traceback; traceback.print_exc()
        account['nextime'] = time.time() + random.randint(10*60, 15*60)
    except Exception, e:
        import traceback; traceback.print_exc()
        account['nextime'] = time.time() + random.randint(10*60, 15*60)
    except XMLSyntaxError, e:
        account['nextime'] = time.time() + random.randint(6*60, 15*60)
    finally:
        if account['status'] not in ('FAILED', 'DONE'):
            account['status'] = 'PENDING'
        account['battle'] = ','.join(map(str, battle_set))
        accountdb.update(**account)
        running_set.remove(int(account['id']))
        print 'finished account:', account['id']

_quit = False
def auto_start():
    while not _quit:
        now = time.time()
        cnt = 0
        for each in accountdb.scan('PENDING'):
            if each['nextime'] <= now:
                cnt += 1
                if cnt > 5:
                    break
                gevent.spawn(run_task, each)
        time.sleep(60)

def web_app(environ, start_response):
    request = Request(environ)
    if request.path == '/':
        template = ('<html><body>'
                    '<form action="/add">add <input name="id" /><input name="pwd" /> '
                    'group:<input name=group /><input type=submit /></form>'
                    '<pre>%s</pre></body></html>')
        content = []
        content.append('<h1>RUNNING</h1><hr />')
        now = time.time()
        for cur in accountdb.scan('RUNNING'):
            cur['mintime'] = datetime.datetime.fromtimestamp(cur['intime'])
            cur['mnextime'] = cur['nextime'] - time.time()
            content.append('%(mintime)s <a href="/log?id=%(id)s">%(id)s</a>:%(invite)s %(name)s lv:%(lv)s '
                    'rounds:%(rounds)s <a href="/stop?id=%(id)s">stop</a>' % cur)
        content.append('<h1>PENDING</h1><hr />')
        for cur in accountdb.scan('PENDING'):
            cur['mintime'] = datetime.datetime.fromtimestamp(cur['intime'])
            cur['mnextime'] = cur['nextime'] - time.time()
            content.append('%(mintime)s <a href="/log?id=%(id)s">%(id)s</a>:%(invite)s %(name)s lv:%(lv)s '
                    'rounds:%(rounds)s %(mnextime)s <a href="/run?id=%(id)s&done=0">run</a> '
                    '<a href="/rm?id=%(id)s">del</a>' % cur)
        content.append('<h1>DONE</h1><hr />')
        done = []
        for cur in accountdb.scan('DONE'):
            cur['mintime'] = datetime.datetime.fromtimestamp(cur['intime'])
            cur['mnextime'] = cur['nextime'] - time.time()
            content.append('%(mintime)s <a href="/log?id=%(id)s">%(id)s</a>:%(invite)s %(name)s lv:%(lv)s '
                    'rounds:%(rounds)s' % cur)
        content.append(' '.join(done))
        content.append('<h1>FAILED</h1><hr />')
        for cur in accountdb.scan('FAILED'):
            cur['mintime'] = datetime.datetime.fromtimestamp(cur['intime'])
            cur['mnextime'] = cur['nextime'] - time.time()
            content.append('%(mintime)s <a href="/log?id=%(id)s">%(id)s</a>:%(invite)s %(name)s lv:%(lv)s '
                    'rounds:%(rounds)s <a href="/run?id=%(id)s&done=0">run</a>' % cur)
        # return 
        start_response("200 OK", [("Content-Type", "text/html")])
        return template % '\n'.join([x.encode('utf8') for x in content])
    elif request.path == '/add':
        _id = request.GET['id']
        pwd = request.GET['pwd']
        group = request.GET['group']
        accountdb.add(_id, pwd, group=group)
        start_response("302 FOUND", [("Location", "/")])
        return 'redirect'
    elif request.path == '/stop':
        _id = int(request.GET['id'])
        if _id in running_set:
            stop_set.add(_id)
            start_response("302 FOUND", [("Location", "/")])
            return 'redirect'
        else:
            start_response("200 OK", [("Content-Type", "text/html")])
            return 'failed!'
    elif request.path == '/rm':
        _id = int(request.GET['id'])
        data = accountdb.get(_id)
        if data:
            data['status'] = 'FAILED'
            accountdb.update(**data)
            start_response("302 FOUND", [("Location", "/")])
            return 'redirect'
        else:
            start_response("200 OK", [("Content-Type", "text/html")])
            return 'failed!'
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
    elif request.path == '/quit':
        global _quit
        _quit = True
        for each in running_set:
            stop_set.add(each)
        start_response("302 FOUND", [("Location", "/")])
        return 'redirect'
    else:
        start_response("404 NOT FOUND", [])
        return '404'

if __name__ == '__main__':
    for each in accountdb.scan('RUNNING'):
        accountdb.update(each['id'], status='PENDING')

    server = gevent.pywsgi.WSGIServer(("", 8888), web_app)
    gevent.spawn(auto_start)
    server.serve_forever()
