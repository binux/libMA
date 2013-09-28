#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-31 14:35:56

import ma
import time
import random
from bot import Bot
from lxml.etree import XMLSyntaxError

class LevelBot(Bot):
    BATTLE_COOLDOWN = 10
    OPERATION_TIME = 0.5
    def login(self, login_id, password, server=None):
        self.login_id = login_id
        self.ma.check_inspection()
        self.ma.notification_post_devicetoken(login_id, password)
        if server:
            self.ma.login(login_id, password, server)
        else:
            self.ma.login(login_id, password)
        assert self.ma.islogin, 'login error!'
        self.ma.mainmenu()
        self.ma.roundtable_edit()

    def _print(self, message):
        print message

    card_prority = {
            124: 0,
            8: 1,
            }
    def compound(self):
        # 124 - 狼娘, 8 - 球女
        cards = []
        for card in self.ma.cards.values():
            if card.master_card_id in self.card_prority:
                cards.append(card)
        if cards:
            card = sorted(cards, key=lambda x: (self.card_prority[x.master_card_id], -x.lv))[0]
        elif self.ma.level > 20:
            self.build_roundtable('battle')
            card = self.ma.roundtable[0]
        else:
            card = None
        if card and card.lv >= card.lv_max:
            card = None

        if card:
            add_cards = [x for x in self.ma.cards.values() if x.rarity <= 3 and x.lv <= 2 and x is not card]
            while add_cards:
                try:
                    self.ma.card_compound(card, add_cards[:30])
                except ma.HeaderError, e:
                    if e.code == 8000:
                        self._print(e.message)
                        break
                time.sleep(self.OPERATION_TIME)
                add_cards = add_cards[30:]
                self._print('compound %slv%s' % (card.name, card.lv))

    LAST_LOGIN_FILTER = (u'今天', u'1日', u'2日', u'3日', u'4日', )
    def scan_player(self, ids):
        for userid in ids:
            try:
                player = self.ma.playerinfo(userid).player_info.user
                time.sleep(self.OPERATION_TIME)
            except Exception, e:
                self._print(e)
                time.sleep(3)
                continue
            if player.last_login in self.LAST_LOGIN_FILTER:
                continue
            if 0 < int(player.deck_rank) < 20: # 单卡
                yield player

    def battle(self, userid):
        ret = self.ma.battle_battle(userid)
        enemy = ret.xpath('//battle_player_list')[1]
        hp = 0
        atk = 0
        for card in enemy.xpath('.//card_list'):
            hp += card.hp
            atk += card.power
        exp_diff = ret.battle_result.before_exp - ret.battle_result.after_exp
        self._print('battle with %s(%s): %s lv:%s bc:%s exp-%s=%s(%s)' % (enemy.name, userid,
            'win' if ret.battle_result.winner else 'lose', self.ma.level, self.ma.bc,
            exp_diff, ret.battle_result.after_exp, float(exp_diff)/self.ma.cost))
        return hp, atk

    def explore(self):
        areas = self.ma.area()
        for _area in areas.xpath('//area_info'):
            if _area.area_type == 1:
                floors = self.ma.floor(_area.id).xpath('//floor_info') 
                _, floor = max([(x.id, x) for x in floors if not x.boss_id])
                area = _area
        self._print('explore area:%s %s%% floor:%s' % (area.name, area.prog_area, floor.id))
        while self.ma.ap > floor.cost:
            ret = self.ma.explore(area.id, floor.id).explore
            self._print('floor:%s event:%s exp-%s=%s%s gold+%s progress=%s%%' % (
                floor.id, ret.event_type, ret.get_exp, ret.next_exp,
                '(LVUP!)' if ret.lvup else '', ret.gold, ret.progress))
            time.sleep(self.OPERATION_TIME)

    def story(self):
        ret = self.ma.story_getoutline()
        #if ret.story_outline.need_level > self.ma.level: #it is checked at client side
            #return
        self._print('story %s' % ret.story_outline.scenario_id)
        try:
            ret = self.ma.start_scenario(0)
        except ma.HeaderError, e:
            ret = self.ma.start_scenario(ret.story_outline.scenario_id)
        if hasattr(ret.scenario, 'sbattle_ready'):
            if self.build_roundtable('high_damage'):
                while self.ma.bc >= self.ma.cost:
                    ret = self.ma.story_battle()
                    if ret.battle_result.winner:
                        self._print('story battle win')
                        return True
                    else:
                        self._print('story battle lose')
                        continue
                return False
            else:
                return False
        ret = self.ma.next_scenario(ret.scenario.phase_id, 0)
        if hasattr(ret.scenario, 'sbattle_ready'):
            if self.build_roundtable('high_damage'):
                while self.ma.bc >= self.ma.cost:
                    ret = self.ma.story_battle()
                    if ret.battle_result.winner:
                        self._print('story battle win')
                        return True
                    else:
                        self._print('story battle lose')
                        continue
                return False
            else:
                return False
        return True

    def task_check(self):
        self.rewards()
        self.friends()
        self.free_point()
        self.gacha()
        self.compound()

    def task_no_bc_action(self):
        self.explore()
        self.story()

if __name__ == '__main__':
    import sys
    from db import battledb
    bot = LevelBot()
    print '----------------------', sys.argv[1], '--------------------------'
    bot.login(sys.argv[1], sys.argv[2])
    bot.report()
    bot.free_point('ap')
    while bot.ma.ap > 5:
        bot.explore()
        bot.free_point('ap')
    #import IPython; IPython.embed()
    #for player in bot.scan_player(range(int(sys.argv[3]), int(sys.argv[4]))):
        #print player.id, unicode(player.name), player.deck_rank, player.leader_card.hp, unicode(player.last_login)
        #battledb.add(player.id, name=unicode(player.name),
                #hp=int(player.leader_card.hp),
                #atk=int(player.leader_card.power),
                #deck_rank=int(player.deck_rank),
                #level=int(player.town_level),
                #leader_card=int(player.leader_card.master_card_id),
                #)
