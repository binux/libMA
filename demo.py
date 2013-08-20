#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-08 00:15:50

import sys
import time
import config
import ma as _ma

FAIRY_BATTLE_COOLDOWN = 20
KEEP_FAIRY = 10*60
SLEEP_TIME = 60
KEEP_BC = 160
touched_fairy = set()
atk_dict = {}

area_id = sys.argv[1] if len(sys.argv) > 1 else None
def main():
    global ma
    global area_id
    ma = _ma.MA()
    ma.login(config.loginId, config.password)
    assert ma.islogin
    ma.my_fairy = False

    def build_roundtable(kill=False, hp=0, atk=0):
        if kill:
            cards = []
            card_masters = set()
            card_hp = 0
            card_cost = 0
            card_atk = [0, 0, 0, 0]
            for card in sorted(ma.cards.values(),
                    key=lambda x: (x.hp+x.power)/x.cost, reverse=True):
                if len(cards) >= 12:
                    break
                if card.master_card_id in card_masters:
                    continue
                cards.append(card)
                card_masters.add(card.master_card_id)
                card_hp += card.hp
                card_cost += card.cost
                card_atk[(len(cards)-1)/3] += card.power

                rounds = (card_hp / atk) + 1
                damage = 0
                card_rounds = len([x for x in card_atk if x > 0])
                for i in range(rounds):
                    damage += card_atk[i%card_rounds]
                if damage > hp and card_cost < ma.bc:
                    print 'changing roundtable(hp:%d damage:%d):' % (card_hp, damage)
                    for i, card in enumerate(cards):
                        if i % 3 == 2:
                            print card.name
                        else:
                            print card.name, '|', 
                    print 
                    ma.save_deck_card(cards)
                    return True
            return False
        elif False and ma.bc - ma.cost > KEEP_BC and not ma.my_fairy:
            top_cards = []
            top_card_masters = set()
            for card in sorted(ma.cards.values(),
                    key=lambda x: (x.hp+x.power)/x.cost, reverse=True):
                if card.master_card_id in top_card_masters:
                    continue
                top_cards.append(card)
                top_card_masters.add(card.master_card_id)

            chose = 0
            while chose < 12:
                chose += 3
                if ma.bc - sum([x.cost for x in top_cards[:chose]]) < KEEP_BC:
                    chose -= 3
                    break
            if chose == 0:
                chose = 3

            print 'changing roundtable:'
            for i in range(0, chose, 3):
                print '%s | %s | %s' % tuple([x.name for x in top_cards[i:i+3]])
            ma.save_deck_card(top_cards[:chose])
            return True
        elif ma.bc - ma.cost >= KEEP_BC:
            return True
        elif ma.bc - ma.cost >= 0 and ma.cost <= 10:
            return True
        else:
            best_cp_card = sorted(ma.cards.values(),
                    key=lambda x: (x.hp+x.power)/x.cost, reverse=True)[0]
            if best_cp_card.cost < ma.bc:
                print 'changing roundtable: %s' % best_cp_card.name
                ma.save_deck_card([best_cp_card, ])
                return True
            min_cost_card = sorted(ma.cards.values(),
                    key=lambda x: (x.cost, -(x.hp+x.power)))[0]
            if ma.bc < min_cost_card.cost:
                return False
            print 'changing roundtable: %s' % min_cost_card.name
            ma.save_deck_card([min_cost_card, ])
            return True

    areas = ma.area()
    if not area_id:
        for area in areas.xpath('//area_info'):
            print '%s %s %s%%' % (area.xpath('id/text()')[0], area.xpath('name/text()')[0], area.xpath('prog_area/text()')[0])
        area_id = raw_input('plaese choose a area to explore: ')
    elif area_id not in areas.xpath('//area_info/id/text()'):
        area_id = max(areas.xpath('//area_info/id/text()'))

    floor_id = 0
    floor_cost = 0
    for floor in ma.floor(area_id).xpath('//floor_info'):
        print "floor:%s progress:%s%% cost:%s" % (floor.xpath('id/text()')[0], floor.xpath('progress/text()')[0], floor.xpath('cost/text()')[0])
        if int(floor.xpath('id/text()')[0]) > floor_id and not int(floor.xpath('boss_id/text()')[0]):
            floor_id = int(floor.xpath('id/text()')[0])
            floor_cost = int(floor.xpath('cost/text()')[0])
    assert floor_id
    print "auto choose floor:%d cost:%d" % (floor_id, floor_cost)

    while True:
        # check fairy
        ma.my_fairy = False
        for fairy_event in ma.fairy_select().xpath('//fairy_event'):
            if fairy_event.xpath('user/id/text()') == ma.user_id:
                ma.my_fairy = True
            if fairy_event.xpath('put_down/text()')[0] != '1':
                continue
            if ma.bc - ma.cost < KEEP_BC and fairy_event.xpath('fairy/serial_id/text()')[0] in touched_fairy:
                continue

            fairy_info = ma.fairy_floor(fairy_event.xpath('fairy/serial_id/text()')[0],
                            fairy_event.xpath('user/id/text()')[0])
            serial_id = fairy_info.xpath('//fairy/serial_id/text()')[0]
            fairy_name = '%slv%s' % (fairy_event.xpath('fairy/name/text()')[0],
                               fairy_event.xpath('fairy/lv/text()')[0])
            if int(fairy_info.xpath('//fairy/hp/text()')[0]) <= 0:
                continue
            if ma.bc - ma.cost < KEEP_BC and ma.user_id in fairy_info.xpath('//attacker/user_id/text()'):
                touched_fairy.add(serial_id)
                continue

            if time.time() - int(fairy_event.xpath('start_time/text()')[0]) > 15*60 and atk_dict.get(fairy_name):
                ret = build_roundtable(kill=True,
                        hp=int(fairy_info.xpath('//fairy/hp/text()')[0]),
                        atk=atk_dict[fairy_name]) or build_roundtable()
            else:
                ret = build_roundtable()
            if ret:
                print "touch fairy: %s by %s" % (fairy_name, fairy_event.xpath('user/name/text()')[0])
                try:
                    battle = ma.fairy_battle(serial_id, fairy_event.xpath('user/id/text()')[0])
                    # battle log
                    result = []
                    fairy = battle.xpath('//battle_vs_info/player')[1]
                    result.append('%s HP:%s ATK:%s -' % (fairy_name, fairy_info.xpath('//fairy/hp/text()')[0],
                                                         fairy.xpath('.//power/text()')[0]))
                    atk_dict[fairy_name] = int(fairy.xpath('.//power/text()')[0])
                    if battle.xpath('//battle_result/winner/text()')[0] != '0':
                        result.append('WINNER!')
                    damage = 0
                    for action in battle.xpath('//battle_action_list'):
                        if action.xpath('attack_damage') and action.xpath('action_player/text()')[0] == '0':
                            damage += int(action.xpath('attack_damage//text()')[0])

                    result.append('damage:%s' % damage)
                    result.append('exp+%s' % (int(battle.xpath('//battle_result/before_exp/text()')[0]) \
                                            - int(battle.xpath('//battle_result/after_exp/text()')[0])))
                    result.append('gold+%s' % (int(battle.xpath('//battle_result/after_gold/text()')[0]) \
                                            - int(battle.xpath('//battle_result/before_gold/text()')[0])))
                    result.append('bikini+%s' % (int(battle.xpath('//battle_result/special_item/after_count/text()')[0]) \
                                            - int(battle.xpath('//battle_result/special_item/before_count/text()')[0])))
                    print ' '.join(result)
                except _ma.HeaderError, e:
                    if e.code != 8000:
                        raise
                    time.sleep(10)
                    continue
                time.sleep(FAIRY_BATTLE_COOLDOWN) # waiting for cooldown? got a can't raise battle error
                
        # explore
        if ma.my_fairy:
            ap_limit = ma.ap_max - 20
        else:
            ap_limit = ma.ap_max / 2
        if ma.ap < ap_limit:
            print "waiting for ap, ap:%d/%d bc:%d/%d" % (ma.ap, ma.ap_max, ma.bc, ma.bc_max)
            time.sleep(SLEEP_TIME)
            continue

        while ma.ap >= ap_limit:
            explore = ma.explore(area_id, floor_id)
            bikini = explore.xpath('//special_item') and \
                        int(explore.xpath('//special_item/before_count/text()')[0]) or 0
            print "exp+%s gold+%s=%s bikini=%s progress:%s%%" % (explore.xpath('.//get_exp/text()')[0],
                                                        explore.xpath('.//gold/text()')[0], ma.gold,
                                                        bikini, explore.xpath('.//progress/text()')[0], ),
            if explore.xpath('explore/lvup/text()')[0] == '1':
                print 'level up!'
            else:
                print "%sexp to go." % explore.xpath('explore/next_exp/text()')[0]

            # event
            if explore.xpath('./explore/fairy') and build_roundtable():
                print "find a fairy: %s lv%s" % (explore.xpath('.//fairy/name/text()')[0], explore.xpath('.//fairy/lv/text()')[0])
                ma.fairy_battle(explore.xpath('.//fairy/serial_id/text()')[0], explore.xpath('.//fairy/discoverer_id/text()')[0])
                touched_fairy.add(explore.xpath('.//fairy/serial_id/text()')[0])
                ma.my_fairy = True
                ap_limit = ma.ap_max - 20
                time.sleep(FAIRY_BATTLE_COOLDOWN)
            if explore.xpath('./explore/next_floor') and explore.xpath('.//next_floor//boss_id/text()')[0] == '0':
                floor_id = int(explore.xpath('.//next_floor/floor_info/id/text()')[0])
                floor_cost = int(explore.xpath('.//next_floor/floor_info/cost/text()')[0])
                print "goto next floor:%s cost:%s" % (floor_id, floor_cost)
            if explore.xpath('./explore/user_card'):
                print "got a card"

if __name__ == '__main__':
    while True:
        try:
            main()
        except _ma.HeaderError, e:
            print e.code, e.message, 'sleep for 10min'
            import traceback; traceback.print_exc()
            time.sleep(10*60)
            continue
        except Exception, e:
            print e.message, 'sleep for 60sec'
            import traceback; traceback.print_exc()
            time.sleep(60)
            continue
            import IPython; IPython.embed()
