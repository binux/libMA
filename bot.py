#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-24 17:46:08

import ma
import random
import time

class Bot(object):
    SLEEP_TIME = 30
    KEEP_FAIRY_TIME = 15*60
    CHOOSE_CARD_LIMIT = 50
    NCARDS_LIMIT = [3, 6, 9, 12, ]
    def __init__(self):
        self.ma = ma.MA()
        self.my_fairy = None
        self.touched_fairies = set()
        self.atk_log = {}

    def _print(self, message):
        print message

    def login(self, login_id, password):
        self.ma.check_inspection()
        self.ma.notification_post_devicetoken(login_id, password)
        self.ma.login(login_id, password)
        assert self.ma.islogin, 'login error!'
        self.ma.mainmenu()
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

    def calc_atk(self, cards, fairy_atk):
        lines = (len(cards)-1)/3+1
        line_hp_combo = (lines-1)*0.05+1
        hp_skill = sum([x.hp*0.2 for x in cards if x.skill_type==2])

        hp = sum([x.hp for x in cards])*line_hp_combo+hp_skill
        atks = [sum([x.power*1.2 if x.skill_type==1 else x.power
                for x in cards[i*3:i*3+3]]) for i in range(0, lines)]
        rounds = int(hp / fairy_atk - 0.00001) + 1
        atk = 0
        for i in range(rounds):
            atk += atks[i%lines]
        return atk

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

    def build_roundtable(self, _type=None, **kwargs):
        if False:
            pass
        elif _type == 'kill':
            hp = kwargs.pop('hp')
            atk = kwargs.pop('atk')
            cards = []
            masters = set()
            for card in sorted([x for x in self.ma.cards.values() if x.lv > 10],
                    key=lambda x: x.hp*x.power, reverse=True)[:self.CHOOSE_CARD_LIMIT]:
                if card.master_card_id in masters:
                    continue
                masters.add(card.master_card_id)
                cards.append(card)

            killed = False
            best_cost = 999
            best_cards = []
            for ncards in self.NCARDS_LIMIT:
                if len(cards)-2 < ncards:
                    break
                for _ in range(min(100, len(cards)*ncards)):
                    cards = list(best_cards) if best_cards else cards
                    for _ in range(ncards*5):
                        switch_a, switch_b = random.randint(0, ncards), random.randint(ncards+1, len(cards)-1)
                        cards[switch_a], cards[switch_b] = cards[switch_b], cards[switch_a]
                        cost = sum([x.cost for x in cards[:ncards]])
                        if best_cost > cost and cost <= self.ma.bc and self.calc_atk(cards[:ncards], atk) >= hp:
                            killed = True
                            best_cards = list(cards)
                            best_cost = cost
                if killed:
                    break
            if not killed:
                return False
            cards = cards[:ncards]
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
        elif _type == 'battle':
            cards = sorted([x for x in self.ma.cards.values() if x.hp>700 and x.power>500],
                        key=lambda x: (x.cost, -x.hp*x.power))[:1]
            if not cards:
                return False
        else:
            return False

        if cards != self.ma.roundtable:
            cards = self.adjust_card_order(cards)
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
        self._print('hp:%s atk:%s damage:%s%s exp-%s=%s gold+%s=%s bikini+%s=%s' % (
                battle.battle_battle.battle_player_list[1].hp, battle.battle_vs_info.player[1].user_card.power,
                sum([x.attack_damage for x in battle.xpath('//battle_action_list') if \
                        hasattr(x, 'attack_damage') and x.action_player == 0]),
                '(win)' if battle_result.winner else '',
                battle_result.before_exp-battle_result.after_exp, battle_result.after_exp,
                battle_result.after_gold-battle_result.before_gold, battle_result.after_gold,
                battle_result.special_item.after_count-battle_result.special_item.before_count,
                battle_result.special_item.after_count))
        self.atk_log[battle.battle_battle.battle_player_list[1].maxhp] = battle.battle_vs_info.player[1].user_card.power
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
                if self.ma.bc < self.ma.bc_max - 20:
                    continue

            # strategy goes here
            ret = False
            if self.ma.bc >= self.ma.bc_max - 20 \
                    and time.time() - fairy_event.start_time > self.KEEP_FAIRY_TIME \
                    and (self.my_fairy is None or fairy.discoverer_id == self.ma.user_id):
                ret = False
                if self.atk_log.get(fairy.hp_max):
                    ret = self.build_roundtable('kill', hp=fairy.hp, atk=self.atk_log[fairy.hp_max])
                ret = ret or self.build_roundtable('high_damage')
            if not ret:
                ret = self.build_roundtable('low_cost')

            if ret:
                self._print('touch fairy: %slv%s by %s' % (fairy.name, fairy.lv, fairy_event.user.name))
                self.battle(fairy.serial_id, fairy.discoverer_id)

    def explore(self):
        if self.my_fairy is not None:
            ap_limit = max(self.ma.ap_max - 20, 20)
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
            self._print('floor:%s event:%s exp-%s=%s%s gold+%s %sprogress=%s%%' % (
                self.floor_id, explore.event_type, explore.get_exp, explore.next_exp,
                '(LVUP!)' if explore.lvup else '', explore.gold, bikini_str, explore.progress))

            # event
            if explore.xpath('./fairy') and self.build_roundtable('low_cost'):
                self._print('find fairy: %slv%s hp:%s' % (explore.fairy.name, explore.fairy.lv, explore.fairy.hp))
                self.battle(explore.fairy.serial_id, explore.fairy.discoverer_id)
                self.my_fairy = explore.fairy
                ap_limit = max(self.ma.ap_max - 20, 20)
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
        self.choose_area(area)
        while True:
            self._print("%s-%s(%s%%): AP:%s/%s BC:%s/%s Gold:%s Cards:%s %s%s%s" % (
                self.ma.name, self.ma.level, self.ma.percentage,
                self.ma.ap, self.ma.ap_max, self.ma.bc, self.ma.bc_max,
                self.ma.gold, len(self.ma.cards),
                "Free Point:%s " % self.ma.free_ap_bc_point if self.ma.free_ap_bc_point else '',
                "Fairy " if self.my_fairy is not None else '',
                "Reward:%s" % getattr(self.ma, 'remaining_rewards', '-')))
            self.fairy()
            self.explore()
            time.sleep(self.SLEEP_TIME)

if __name__ == '__main__':
    import sys
    import config
    bot = Bot()
    while True:
        try:
            bot.run(config.loginId, config.password, int(sys.argv[1]) if len(sys.argv) > 1 else None)
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
