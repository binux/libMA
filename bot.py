#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-24 17:46:08

import ma
import time

class Bot(object):
    SLEEP_TIME = 30
    KEEP_FAIRY_TIME = 15*60
    def __init__(self):
        self.ma = ma.MA()
        self.my_fairy = None
        self.fairy_battle_cool_down = 0
        self.touched_fairies = set()

    def _print(self, message):
        print message

    def login(self, login_id, password):
        self.ma.login(login_id, password)
        assert self.ma.islogin, 'login error!'
        self.ma.masterdata_card()
        self.ma.roundtable_edit()

    def choose_area(self, area_id=None):
        areas = self.ma.area()
        for area in areas.xpath('//area_info'):
            self._print('%s %s %s' % (area.id, area.name, area.prog_area))
        if area_id and str(area_id) not in areas.xpath('//area_info/id/text()'):
            area_id = None
        if not area_id:
            for area in areas.xpath('//area_info'):
                if area.prog_area < 100:
                    area_id = area.id
                    break
        else:
            for area in areas.xpath('//area_info'):
                if area.id == area_id:
                    break
        self.area_id = area_id

        floors = self.ma.floor(area_id).xpath('//floor_info') 
        _, floor = max([(x.id, x) for x in floors if not x.boss_id])
        self._print('choose area:%s-%s' % (area.name, floor.id))
        self.floor_id = floor.id
        self.floor_cost = floor.cost

    def build_roundtable(self, _type=None, **kwargs):
        if False:
            pass
        elif _type == 'kill':
            return False
        elif _type == 'high_damage':
            cards = []
            masters = set()
            for card in sorted(self.ma.cards.values(),
                    key=lambda x: x.power, reverse=True):
                if card.master_card_id in masters:
                    continue
                masters.add(card.master_card_id)
                cards.append(card)
                if len(cards) == 3:
                    break
            if sum([x.cost for x in cards]) > self.ma.bc:
                return False
        elif _type == 'low_cost' or not _type:
            min_cost_card = sorted(self.ma.cards.values(),
                    key=lambda x: (x.cost, -(x.hp+x.power)))[0]
            if self.ma.bc < min_cost_card.cost:
                return False
            cards = [min_cost_card, ]
        else:
            return False

        if [x.serial_id for x in cards] != [x.serial_id for x in self.ma.roundtable]:
            self._print('changing roundtable: %s cost: %s' % (' | '.join([x.name for x in cards]),
                                                              sum([x.cost for x in cards])))
            self.ma.save_deck_card(cards)
        return True

    def battle(self, serial_id, user_id):
        try:
            battle = self.ma.fairy_battle(serial_id, user_id)
        except ma.HeaderError, e:
            if e.code not in (8000, 1010):
                raise
            time.sleep(10)
            return False
        self.touched_fairies.add(serial_id)
        battle_result = battle.battle_result
        self._print('hp:%s atk:%s damage:%s%s exp-%s=%s glod+%s=%s bikini+%s=%s' % (
                battle.battle_battle.battle_player_list[1].hp, battle.battle_vs_info.player[1].user_card.power,
                sum([x.attack_damage for x in battle.xpath('//battle_action_list') if \
                        hasattr(x, 'attack_damage') and x.action_player == 0]),
                '(win)' if battle_result.winner else '',
                battle_result.before_exp-battle_result.after_exp, battle_result.after_exp,
                battle_result.after_gold-battle_result.before_gold, battle_result.after_gold,
                battle_result.special_item.after_count-battle_result.special_item.before_count,
                battle_result.special_item.after_count))
        return True

    def fairy(self):
        self.my_fairy = None
        for fairy_event in sorted(self.ma.fairy_select().xpath('//fairy_event'),
                                key=lambda x: (x.fairy.serial_id in self.touched_fairies,
                                               x.user.id != self.ma.user_id,
                                               x.start_time, x.fairy.lv, )):
            if fairy_event.put_down != 1: # killed
                continue
            if fairy_event.user.id == self.ma.user_id:
                fairy_event.fairy.discoverer_id = fairy_event.user.id
                self.my_fairy = fairy_event.fairy
            if self.ma.bc < self.ma.bc_max - 1 and fairy_event.fairy.serial_id in self.touched_fairies: # touched
                continue

            fairy = self.ma.fairy_floor(fairy_event.fairy.serial_id, fairy_event.user.id).xpath('//explore/fairy')[0]
            if fairy.hp <= 0: # killed
                continue
            if str(self.ma.user_id) in fairy.xpath('//attacker/user_id/text()'):
                self.touched_fairies.add(fairy.serial_id)
                if self.ma.bc < self.ma.bc_max - 1:
                    continue

            # strategy goes here
            ret = False
            if self.ma.bc >= self.ma.bc_max - 1 \
                    and time.time() - fairy_event.start_time > self.KEEP_FAIRY_TIME \
                    and (not self.my_fairy or fairy.discoverer_id == self.ma.user_id):
                ret = self.build_roundtable('kill') or self.build_roundtable('high_damage')
            if not ret:
                ret = self.build_roundtable('low_cost')

            if ret:
                self._print('touch fairy: %slv%s by %s' % (fairy.name, fairy.lv, fairy_event.user.name))
                self.battle(fairy.serial_id, fairy.discoverer_id)

    def explore(self):
        if self.my_fairy is not None:
            ap_limit = self.ma.ap_max - 1
        else:
            ap_limit = min(self.ma.ap_max / 2, 20)
        if self.ma.ap < ap_limit:
            return

        while self.ma.ap >= ap_limit:
            explore = self.ma.explore(self.area_id, self.floor_id).explore
            
            bikini_str = ''
            if hasattr(explore, 'special_item') and explore.special_item.after_count:
                bikini_str = 'bikini+%s=%s ' % (explore.special_item.after_count - explore.special_item.before_count,
                        explore.special_item.after_count)
            self._print('floor:%s event:%s exp-%s=%s%s glod+%s %sprogress=%s%%' % (
                self.floor_id, explore.event_type, explore.get_exp, explore.next_exp,
                '(LVUP!)' if explore.lvup else '', explore.gold, bikini_str, explore.progress))

            # event
            if explore.xpath('./fairy') and self.build_roundtable('low_cost'):
                self._print('find fairy: %slv%s hp:%s' % (explore.fairy.name, explore.fairy.lv, explore.fairy.hp))
                self.battle(explore.fairy.serial_id, explore.fairy.discoverer_id)
                self.my_fairy = explore.fairy
                ap_limit = self.ma.ap_max - 1
            if explore.xpath('./next_floor') and explore.next_floor.floor_info.boss_id == 0:
                self.floor_id = explore.next_floor.floor_info.id
                self.floor_cost = explore.next_floor.floor_info.cost
                self._print('next floor: %s cost:%s' % (self.floor_id, self.floor_cost))
            if explore.xpath('./user_card'):
                card_id = explore.user_card.master_card_id
                master_card = self.ma.master_cards[card_id]
                if master_card:
                    self._print('got card: %s-%s%s' % (master_card['name'], master_card['rarity'],
                        ' (HOLO!)' if explore.user_card.holography else '' ))

    def run(self, login_id, password, area=None):
        self.login(login_id, password)
        self.choose_area(int(area))
        while True:
            self._print('current AP:%s/%s BC:%s/%s' % (self.ma.ap, self.ma.ap_max, self.ma.bc, self.ma.bc_max))
            self.fairy()
            self.explore()
            time.sleep(self.SLEEP_TIME)

if __name__ == '__main__':
    import sys
    import config
    bot = Bot()
    while True:
        try:
            bot.run(config.loginId, config.password, sys.argv[1] if len(sys.argv) > 1 else None)
        except ma.HeaderError, e:
            print e.code, e.message, 'sleep for 10min'
            import traceback; traceback.print_exc()
            time.sleep(10*60)
            continue
        except Exception, e:
            print e, 'sleep for 1min'
            import traceback; traceback.print_exc()
            time.sleep(60)
            continue
