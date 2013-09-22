#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-09-19 01:29:31

import sys
import time
import config
from bot import Bot

class FangYaoBot(Bot):
    AP_LIMIT = 0

    def choose_area(self, area_id=None):
        areas = self.ma.area()
        _area = None
        for area in areas.xpath('//area_info'):
            if area.area_type == 1:
                area_id = area.id
                _area = area
                break
        self.area_id = area_id

        floors = self.ma.floor(area_id).xpath('//floor_info') 
        _, floor = min([(x.cost, x) for x in floors if not x.boss_id])
        self._print('choose area:%s-%s cost:%s' % (_area.name, floor.id, floor.cost))
        self.floor_id = floor.id
        self.floor_cost = floor.cost

class JueXingBot(Bot):
    def _print(self, msg):
        print '--->', msg

    def _fairy(self, friend_user_id):
        for fairy_event in self.ma.fairy_select().xpath('//fairy_event'):
            if fairy_event.put_down != 1: # killed
                continue
            if fairy_event.user.id == self.ma.user_id:
                if u'觉醒的' in unicode(fairy_event.fairy.name):
                    raw_input('my rare fairy fo_idund, wait')
                    return True
                else:
                    self._print('my fairy found, break')
                    return False
            if fairy_event.user.id not in (friend_user_id, self.ma.user_id):
                continue

            fairy_event.fairy.discoverer_id = fairy_event.user.id
            fairy = self.ma.fairy_floor(fairy_event.fairy.serial_id, fairy_event.user.id).xpath('//explore/fairy')[0]
            #fairy.rare_flg
            if fairy.hp <= 0: # killed
                continue

            if fairy.lv < 3:
                ret = self.build_roundtable('fairy_lv2')
            else:
                ret = self.build_roundtable('fairy_lv3')

            if ret:
                self._print('touch fairy: %slv%s by %s' % (fairy.name, fairy.lv, fairy_event.user.name))
                ret = self.battle(fairy.serial_id, fairy.discoverer_id)
                if ret is False:
                    pass
                elif hasattr(ret.explore, 'rare_fairy'): #juexing
                    rare_fairy = ret.explore.rare_fairy
                    fairy = self.ma.fairy_floor(rare_fairy.serial_id, self.ma.user_id).xpath('//explore/fairy')[0]
                    self._print('!!touch fairy: %slv%s by %s' % (fairy.name, fairy.lv, fairy_event.user.name))
                    ret = self.build_roundtable('high_damage')
                    if ret:
                        self.battle(fairy.serial_id, fairy.discoverer_id)
                        return True
                elif ret.battle_result.winner:
                    return True
            return False

if __name__ == '__main__':
    main_bot = JueXingBot()
    main_bot.login(config.loginId, config.password)
    while True:
        main_bot.fairy()
        _input = raw_input('login_id password:')
        if not _input:
            break
        login_id, password = _input.split()

        bot = FangYaoBot()
        bot.AP_LIMIT = 0
        bot.login(login_id, password)
        bot.friends(bot.ma.friend_max-1)

        friendlist = bot.ma.friendlist()
        is_friend = False
        for user in friendlist.xpath('//user'):
            if user.id == main_bot.ma.user_id:
                is_friend = True

        if not is_friend and bot.ma.friends >= bot.ma.friend_max:
            bot.ma.remove_friend(ret.xpath('//user')[0].id)
            print "max friends, removed one, use this account tomorrow"
            continue

        if not is_friend:
            bot.ma.add_friend(main_bot.ma.user_id)
            main_bot.ma.approve_friend(bot.ma.user_id)
            main_bot.free_point('bc')
            main_bot.sell_cards()
        bot.choose_area()
        bot.free_point('ap')
        while True:
            bot.fairy()
            bot.explore(next_floor=False, next_area=False)
            bot.report()
            if not main_bot._fairy(bot.ma.user_id):
                bot.ma.remove_friend(main_bot.ma.user_id)
                break
            main_bot.report()
            if bot.ma.ap < bot.floor_cost:
                bot.ma.remove_friend(main_bot.ma.user_id)
                break
