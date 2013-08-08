#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-08 00:15:50

import time
import config
import ma as _ma

sleep_time = 3*60
touched_fairy = set()

def main():
    global ma
    ma = _ma.MA()
    ma.login(config.loginId, config.password)
    assert ma.islogin

    for area in ma.area().xpath('//area_info'):
        print '%s %s %s%%' % (area.xpath('id/text()')[0], area.xpath('name/text()')[0], area.xpath('prog_area/text()')[0])
    area_id = raw_input('plaese choose a area to explore: ')

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
        for fairy_event in ma.fairy_select().xpath('//fairy_event'):
            if fairy_event.xpath('put_down/text()')[0] == '1' \
                    and fairy_event.xpath('fairy/serial_id/text()')[0] not in touched_fairy \
                    and ma.user_id not in ma.fairy_floor(fairy_event.xpath('fairy/serial_id/text()')[0],
                            fairy_event.xpath('user/id/text()')[0]).xpath('//attacker/user_id/text()') \
                    and ma.bc > 20:
                print "touch fairy: %slv%s by %s" % (fairy_event.xpath('fairy/name/text()')[0],
                                                      fairy_event.xpath('fairy/lv/text()')[0],
                                                      fairy_event.xpath('user/name/text()')[0])
                ma.fairy_battle(fairy_event.xpath('fairy/serial_id/text()')[0], fairy_event.xpath('user/id/text()')[0])
                touched_fairy.add(fairy_event.xpath('fairy/serial_id/text()')[0])
                
        # explore
        if ma.ap_max - ma.ap >= floor_cost:
            print "waiting for ap, current:%d/%d" % (ma.ap, ma.ap_max)
            time.sleep(sleep_time)
            ma.mainmenu()
            continue
        explore = ma.explore(area_id, floor_id)
        print "exp+%s gold+%s=%s progress:%s%%" % (explore.xpath('.//get_exp/text()')[0],
                                                    explore.xpath('.//gold/text()')[0], ma.gold,
                                                    explore.xpath('.//progress/text()')[0], ),
        if explore.xpath('.//lvup/text()')[0] == '1':
            print 'level up!'
        else:
            print "%sexp to go." % explore.xpath('.//next_exp/text()')[0]

        # event
        if explore.xpath('./explore/fairy'):
            print "find a fairy: %s lv%s" % (explore.xpath('.//fairy/name/text()')[0], explore.xpath('.//fairy/lv/text()')[0])
            ma.fairy_battle(explore.xpath('.//fairy/serial_id/text()')[0], explore.xpath('.//fairy/discoverer_id/text()')[0])
            touched_fairy.add(explore.xpath('.//fairy/serial_id/text()')[0])
        if explore.xpath('./explore/next_floor') and explore.xpath('.//next_floor/boos_id/text()')[0] == '0':
            floor_id = int(explore.xpath('.//next_floor/floor_info/id/text()')[0])
            floor_cost = int(explore.xpath('.//next_floor/floor_info/cost/text()')[0])
            print "goto next floor:%s cost:%s" % (floor_id, floor_cost)
        if explore.xpath('./explore/user_card'):
            print "got a card"

if __name__ == '__main__':
    try:
        main()
    except _ma.HeaderError, e:
        print e
        time.sleep(30*60)
    except Exception, e:
        print e
        import IPython; IPython.embed()
