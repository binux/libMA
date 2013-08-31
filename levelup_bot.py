#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-31 14:35:56

import ma
import random
import time

class LevelBot(object):
    def __init__(self):
        self.ma = ma.MA()
        self.story_blocked = False

    def login(self, login_id, password):
        self.login_id = login_id
        self.ma.check_inspection()
        self.ma.notification_post_devicetoken(login_id, password)
        self.ma.login(login_id, password)
        assert self.ma.islogin, 'login error!'
        self.ma.mainmenu()
        self.ma.roundtable_edit()

    def _print(self, message):
        print message

    def rewards(self):
        ret = self.ma.rewardbox()
        ids = ret.xpath('//rewardbox/id/text()')
        while ids:
            ret = self.ma.get_rewards(ids[:20])
            self._print('get reward')
            ids = ids[20:]

    def friends(self):
        ret = self.ma.friend_notice()
        for user in ret.xpath('//user'):
            if self.ma.friends < self.ma.friend_max:
                self.ma.approve_friend(user.id)
                self._print('approve friend: %s' % user.name)
            else:
                self.ma.refuse_friend(user.id)
                self._print('refuse friend: %s' % user.name)
        #if self.ma.friends < self.ma.friend_max:
            #self.ma.add_friend(userid)

    def free_point(self):
        if self.ma.free_ap_bc_point > 0:
            self._print('set point')
            self.ma.pointsetting(ap=0, bc=self.ma.free_ap_bc_point)

    def gacha(self):
        while self.ma.gacha_ticket:
            self._print('gacha')
            self.ma.gacha_buy(0, 0, 2)
        while self.ma.friendship_point > 200:
            self._print('friendship point')
            self.ma.gacha_buy(1, 0, 1)

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
            add_cards = [x for x in self.ma.cards.values() if x.rarity <= 3 and x.lv <= 2 and x is not card]
            while add_cards:
                try:
                    self.ma.card_compound(card, add_cards[:30])
                except ma.HeaderError, e:
                    if e.code == 8000:
                        self._print(e.message)
                        break
                add_cards = add_cards[30:]
                self._print('compound %slv%s' % (card.name, card.lv))

    LAST_LOGIN_FILTER = (u'今天', u'1日', u'2日', u'3日', u'4日', )
    def scan_player(self, ids):
        for userid in ids:
            player = self.ma.playerinfo(userid).player_info.user
            if player.last_login in self.LAST_LOGIN_FILTER:
                continue
            if player.deck_rank > 20: # 单卡
                continue
            yield player

    def adjust_card_order(self, cards):
        lines = (len(cards)-1)/3+1
        atk_cards = [x for x in cards if x.skill_type==1]
        hp_cards = [x for x in cards if x.skill_type==2]
        other_cards = [x for x in cards if x.skill_type not in (1, 2)]
        _cards = atk_cards+other_cards+hp_cards
        cards = []
        for line in range(lines):
            for i in range(3):
                pos = lines*i+line
                if pos < len(_cards):
                    cards.append(_cards[pos])
        return cards

    def build_roundtable(self, _type=None):
        if _type == 'damage':
            cards = []
            masters = set()
            for card in sorted(self.ma.cards.values(),
                    key=lambda x: x.hp*x.power, reverse=True):
                if card.master_card_id in masters:
                    continue
                masters.add(card.master_card_id)
                cards.append(card)
                if len(cards) == 3:
                    break
            if sum([x.cost for x in cards]) > self.ma.bc:
                return False
        else:
            cards = sorted([x for x in self.ma.cards.values() if x.hp>700 and x.power>500],
                        key=lambda x: (x.cost, -x.hp*x.power))[:1]
            if not cards:
                return False

        cards = self.adjust_card_order(cards)
        if cards != self.ma.roundtable:
            self._print('changing roundtable: %s cost: %s' % (' | '.join([x.name for x in cards]),
                                                              sum([x.cost for x in cards])))
            self.ma.save_deck_card(cards)
        return True

    def battle(self, userid):
        ret = self.ma.battle_battle(userid)
        enemy = ret.xpath('//battle_player_list')[1]
        hp = 0
        atk = 0
        for card in enemy.xpath('//card_list'):
            hp += card.hp
            atk += card.power
        self._print('battle with %s: %s' % (enemy.name, 'win' if ret.battle_result.winner else 'lose'))
        return hp, atk

    def explore(self):
        areas = self.ma.area()
        for area in areas.xpath('//area_info'):
            if area.prog_area < 100:
                floors = self.ma.floor(area.id).xpath('//floor_info') 
                _, floor = max([(x.id, x) for x in floors if not x.boss_id])
                break
        self._print('explore area:%s %s%% floor:%s' % (area.name, area.prog_area, floor.id))
        while self.ma.ap > floor.cost:
            ret = self.ma.explore(area.id, floor.id).explore
            self._print('floor:%s event:%s exp-%s=%s%s gold+%s progress=%s%%' % (
                floor.id, ret.event_type, ret.get_exp, ret.next_exp,
                '(LVUP!)' if ret.lvup else '', ret.gold, ret.progress))

    def story(self):
        ret = self.ma.story_getoutline()
        while not self.story_blocked and ret.story_outline.need_level <= self.ma.level:
            self._print('story %s' % ret.story_outline.scenario_id)
            ret = self.ma.start_scenario(ret.story_outline.scenario_id)
            if hasattr(ret.scenario, 'sbattle_ready'):
                if self.build_roundtable('damage'):
                    ret = self.ma.story_battle()
                    if ret.battle_result.winner:
                        self._print('story battle win')
                        continue
                    else:
                        self._print('story battle lose')
                        self.story_blocked = True
                        break
                else:
                    self._print("can't finished story battle")
                    self.story_blocked = True
                    break
            if ret.scenario.phase_id and not self.build_roundtable('damage'):
                self._print("can't build roundtable")
                break
            ret = self.ma.next_scenario(ret.scenario.phase_id, 0)
            if hasattr(ret.scenario, 'sbattle_ready'):
                ret = self.ma.story_battle()
                if ret.battle_result.winner:
                    self._print('story battle win')
                else:
                    self._print('story battle lose')
                    self.story_blocked = True
                    break
            ret = self.ma.story_getoutline()

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
    bot.login(sys.argv[1], sys.argv[2])
    for player in bot.scan_player(range(int(sys.argv[3]), int(sys.argv[4]))):
        print player.id, unicode(player.name), player.deck_rank, player.leader_card.hp, unicode(player.last_login)
        battledb.add(player.id, name=unicode(player.name),
                hp=player.leader_card.hp,
                atk=player.leader_card.power,
                deck_rank=player.deck_rank)
