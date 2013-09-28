#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-12 11:45:18

import config
from ma import MA

def sort_card(by, reverse=True):
    ma = MA()
    login = ma.login(config.loginId, config.password)
    ma.masterdata_card()
    for card in ma.cards.values():
        card.hp_power = card.hp + card.power
        card.cp =  card.hp_power / card.cost
        card.lvmax_hp_power = card.lvmax_hp + card.lvmax_power
        card.lvmax_cp = card.lvmax_hp_power / card.cost

    return sorted(ma.cards.values(), key=lambda x: getattr(x, by),
            reverse=reverse)

if __name__ == '__main__':
    import sys
    by = 'cp'
    limit = 50
    for key in sys.argv[1:]:
        if key.isdigit():
            limit = int(key)
        elif key in ('cp', 'hp_power', 'lvmax_hp_power', 'lvmax_cp', 'hp', 'power',
                     'rarity', 'sale_price', 'max_lv', 'lvmax_power', 'lvmax_hp', 'lv'):
            by = key

    for card in sort_card(by, limit):
        string = u"%s %s-%d lv%d/%d %s=%s" % (card.serial_id, card.name, card.rarity, card.lv, card.lv_max,
                                   by, getattr(card, by))
        print string.encode('utf8')
