#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-08 00:15:50

import time
import config
from ma import MA

sleep_time = 3*60
touched_fairy = set()

def main():
    ma = MA()
    ma.login(config.loginId, config.password)
    assert ma.islogin

    for area in ma.area().xpath('//area_info'):
        print area.xpath('id/text()'), area.xpath('name/text()')
    area_id = raw_input('plaese choose a area to explore: ')

    floor_id = 0
    floor_cost = 0
    for floor in ma.floor(area_id).xpath('//floor_info'):
        print "floor%s progress:%s%% cost:%s%%" % (floor.xpath('id/text()'), floor.xpath('progress/text()'), floor.xpath('cost/text()'))
        if int(floor.xpath('id/text()')) > floor_id and not int(floor.xpath('boss_id/text()')):
            floor_id = int(floor.xpath('id/text()'))
            floor_cost = int(floor.xpath('cost/text()'))
    print "auto choose floor%d cost:%d" % (floor_id, floor_cost)

    while True:
        # check fairy
        for fairy_event in ma.fairy_select().xpath('//fairy_event'):
            if fairy_event.xpath('fairy/put_down/text()') == '1' \
                    and fairy_event.xpath('fairy/serial_id/text()') not in touched_fairy \
                    and ma.bc > 20:
                print "touch fairy: %s lv%s by %s" % (fairy_event.xpath('fairy/name/text()'),
                                                      fairy_event.xpath('fairy/lv/text()'),
                                                      fairy_event.xpath('user/name/text()'))
                ma.fairy_battle(fairy_event.xpath('fairy/serial_id/text()'), fairy_event.xpath('user/id/text()'))
                touched_fairy.add(fairy_event.xpath('fairy/serial_id/text()'))
                
        # explore
        if ma.ap_max - ma.ap >= floor_cost:
            print "waiting for ap"
            time.sleep(60)
            continue
        explore = ma.explore(area_id, floor_id)
        print "exp+%s gold+%s progress:%s%%" % (explore.xpath('get_exp/text()'), explore.xpath('gold/text()'),
                                                explore.xpath('progress/text()'), )
        if explore.xpath('lvup/text()') == '1':
            print ' level up!'
        else:
            print " %sexp to go." % explore.xpath('next_exp/text()')

        # event
        if explore.xpath('./explore/fairy'):
            print "find a fairy: %s lv%s" % (explore.xpath('fairy/name/text()'), explore.xpath('fairy/lv/text()'))
            ma.fairy_battle(explore.xpath('fairy/serial_id/text()'), explore.xpath('fairy/discoverer_id/text()'))
            touched_fairy.add(explore.xpath('fairy/serial_id/text()'))
        if explore.xpath('./explore/next_floor') and explore.xpath('next_floor/boos_id/text()') == '0':
            print "goto next floor"
            floor_id = int(explore.xpath('next_floor/id/text()'))
            floor_cose = int(explore.xpath('next_floor/cost/text()'))
        if explore.xpath('./explore/user_card'):
            print "got a card"

if __name__ == '__main__':
    main()
