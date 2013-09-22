#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-09-19 12:07:45

import os
import sys
import config
from bot import Bot

if __name__ == '__main__':
    bot = Bot()
    bot.login(config.loginId, config.password)
    ok = False
    while not ok:
        bot.fairy()
        bot.report()
        bot.fairy_rewards()
        bot.sell_cards()
        base_card = bot.ma.cards[int(sys.argv[1])]
        ok = bot.compound(base_card, 110)
