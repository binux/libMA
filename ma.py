#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-05 23:58:01

import re
import time
import json
import random
import config
import requests
from lxml import objectify, etree
from urlparse import urljoin
from HttpUtils import _cryptParams
from CryptUtils import crypt

class HeaderError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __repr__(self):
        return "HeaderError(code=%r, message=%r)" % (self.code, self.message)

    def __str__(self):
        return self.message.encode('utf8')

    def __unicode__(self):
        return self.message

class Card:
    """
    attrs:
        critical
        evolution_price
        exp
        exp_diff
        exp_per
        holography
        hp
        limit_over
        lv
        lv_max
        ma
        master_card_id
        material_price
        max_exp
        next_exp
        plus_limit_count
        power
        sale_price
        serial_id
    """
    ma = None

    @classmethod
    def from_xml(cls, card):
        c = cls()
        for node in card.iterchildren():
            setattr(c, node.tag, int(node.text))
        return c

    def set_ma(self, ma):
        self.ma = ma
        return self

    def __getattr__(self, key):
        if self.ma and self.__dict__['master_card_id'] in self.ma.master_cards \
                and key in self.ma.master_cards[self.master_card_id]:
            return self.ma.master_cards[self.master_card_id][key]
        raise AttributeError(key)

class MA:
    default_http_header = {
            'User-Agent': config.USER_AGENT,
            'Accept-Encoding': 'gzip, deflate',
            }
    HOME = 'connect/app'
    BASE_URL = config.BASE_URL
    FAIRY_BATTLE_COOLDOWN = 20

    def __init__(self):
        self.device_id = ''.join([str(random.randint(0, 9)) for x in range(15)])
        self.session = requests.Session()
        self.session.headers.update(self.default_http_header)
        self.session_id = None
        self.fairy_battle_cooldown = 0
        self.your_data = {}

    @property
    def islogin(self):
        return bool(self.session_id)

    @property
    def level(self):
        return self.town_level

    @property
    def ap(self):
        now = time.time()
        return self._ap + int((now - self.ap_last_update_time) / self.ap_interval_time)

    @property
    def bc(self):
        now = time.time()
        return self._bc + int((now - self.bc_last_update_time) / self.bc_interval_time)

    def abs_path(self, path):
        if path.startswith('~'):
            path = path.replace('~', self.HOME)
        return urljoin(self.BASE_URL, path)

    def cat(self, resource, params={}, **kwargs):
        kwargs.update(params)
        params = _cryptParams(kwargs)
        response = self.session.post(self.abs_path(resource), params, params={"cyt": 1})
        return crypt.decode(response.content)

    def parse_header(self, header):
        error_code = int(header.xpath('./error/code/text()')[0])
        if error_code:
            self.session_id = None
            raise HeaderError(error_code, unicode(header.xpath('./error/message/text()')[0]))

        self.session_id = header.xpath('./session_id/text()')[0]

        your_data = header.xpath('./your_data')
        if your_data:
            your_data = your_data[0]

            for attr in ('name', 'leader_serial_id/i', 'town_level/i', 'percentage/i',
                         'gold/i', 'cp/i', 'max_card_num/i', 'free_ap_bc_point/i',
                         'friendship_point/i', 'country_id/i', 'ex_gauge/i',
                         'gacha_ticket/i', 'deck_rank/i', 'friends/i', 'friend_max/i',
                         'friends_invitations/i', 'notice_of_menu/i', 'gacha_point/i',
                         'fairy_appearance/i', 'next_scene/i', ):
                if attr.endswith('/i'):
                    attr = attr[:-2]
                    make_up = int
                else:
                    make_up = lambda x: x
                data = your_data.xpath('./%s/text()' % attr)
                if data:
                    setattr(self, attr, make_up(data[0]))

            if your_data.xpath('./ap'):
                self._ap = int(your_data.xpath('./ap/current/text()')[0])
                self.ap_max = int(your_data.xpath('./ap/max/text()')[0])
                self.ap_interval_time = int(your_data.xpath('./ap/interval_time/text()')[0])
                self.ap_last_update_time = int(your_data.xpath('./ap/last_update_time/text()')[0])
            if your_data.xpath('./bc'):
                self._bc = int(your_data.xpath('./bc/current/text()')[0])
                self.bc_max = int(your_data.xpath('./bc/max/text()')[0])
                self.bc_interval_time = int(your_data.xpath('./bc/interval_time/text()')[0])
                self.bc_last_update_time = int(your_data.xpath('./bc/last_update_time/text()')[0])

            if your_data.xpath('./owner_card_list'):
                self.cards = {}
                for card in your_data.xpath('./owner_card_list/user_card'):
                    card = Card.from_xml(card).set_ma(self)
                    self.cards[card.serial_id] = card
            if your_data.xpath('./itemlist'):
                self.iterms = {}
                for item in your_data.xpath('./itemlist'):
                    self.iterms[item.xpath('./item_id/text()')[0]] = int(item.xpath('./num/text()')[0])

    def get(self, resource, params={}, **kwargs):
        kwargs.update(params) # params has a same object, don't update it
        data = self.cat(resource, params=kwargs)
        try:
            xml = objectify.fromstring(data)
        except Exception, e:
            e.message = data
            raise
        self.last_xml = xml
        if config.DEBUG:
            with open("resource/"+resource.replace('~/', '').replace('/', '_'), 'w') as fp:
                fp.write(etree.tostring(xml, pretty_print=True))

        self.parse_header(xml.xpath('/response/header')[0])

        return xml.xpath('/response/body')[0]

    def wordlist(self):
        return self.session.post("http://dlc.game-CBT.ma.sdo.com:50005/world_list.php", data={"data_str": '{"device_id":"'+self.device_id+'"}'}).json

    def check_inspection(self):
        return self.cat("~/check_inspection")

    def notification_post_devicetoken(self, login_id, password, token=config.deviceToken, S="nosessionid"):
        return self.cat("~/notification/post_devicetoken", login_id=login_id, password=password, token=token, S=S) 

    def regist(self, login_id, password, invitation_id, platform=2, device_id=None):
        if device_id is None:
            device_id = self.device_id
        return self.get("~/regist", login_id=login_id, password=password, invitation_id=invitation_id,
                        platform=platform, param=device_id)

    def save_character(self, name, country=1):
        return self.get("~/tutorial/save_character", name=name, country=country)

    def login(self, login_id, password):
        body = self.get("~/login", login_id=login_id, password=password)
        self.user_id = (body.xpath('./login/user_id/text()') or [None, ])[0]
        return body

    def masterdata_card(self):
        resource = "~/masterdata/card/update"
        data = self.cat(resource)
        # fix format bug here
        data = re.sub("&(?!amp;)", "&amp;", data)
        xml = etree.fromstring(data)
        self.last_xml = xml
        if config.DEBUG:
            with open("resource/"+resource.replace('~/', '').replace('/', '_'), 'w') as fp:
                fp.write(etree.tostring(xml, pretty_print=True))

        self.parse_header(xml.xpath('/response/header')[0])

        body = xml.xpath('/response/body')[0]

        # save it
        self.master_cards = {}
        for each in body.xpath('//card'):
            card = {}
            for attr in ('character_id/i', 'base_hp/i', 'extra/i', 'base_holo_hp/i', 'base_power/i',
                         'cost/i', 'char_description', 'attack_type/i', 'card_version/i', 'country_id/i',
                         'lvmax_holo_power/i', 'image1_id/i', 'sale_price/i', 'compound_type/i', 'max_lv/i',
                         'skill_kana', 'max_lv_holo/i', 'eye_y/i', 'lvmax_holo_hp/i', 'form_id/i', 'data_type/i',
                         'lvmax_hp/i', 'growth_rate_text', 'lvmax_power/i', 'grow_name', 'grow_type/i',
                         'distinction/i', 'skill_type/i', 'base_holo_power/i', 'skill_name', 'image2_id/i',
                         'illustrator', 'name', 'master_card_id/i', 'rarity/i', 'skill_description'):
                if attr.endswith('/i'):
                    attr = attr[:-2]
                    make_up = int
                else:
                    make_up = lambda x: x
                data = each.xpath('./%s/text()' % attr)
                if data:
                    card[attr] = make_up(data[0])
            self.master_cards[card['master_card_id']] = card

        return body

    def mainmenu(self):
        return self.get("~/mainmenu")

    def menulist(self):
        return self.get("~/menu/menulist")

    def playerinfo(self, user_id=None, kind=6): # kind: 1=other 6=self
        if not user_id:
            user_id = self.user_id
        return self.get("~/menu/playerinfo", user_id=user_id, kind=kind)

    def friendlist(self, move=0):
        return self.get("~/menu/friendlist", move=move)

    def other_list(self):
        return self.get("~/menu/other_list")

    def rewardbox(self):
        return self.get("~/menu/rewardbox")

    def get_rewards(self, notice_id):
        if isinstance(notice_id, list):
            return ",".join(map(str, notice_id))
        return self.get("~/menu/get_rewards", notice_id=notice_id)

    def goodlist(self, user_id=None):
        if not user_id:
            user_id = self.user_id
        return self.get("~/menu/goodlist", user_id=user_id)

    def battlehistory(self):
        return self.get("~/menu/battlehistory")

    def cardcollection(self):
        return self.get("~/menu/cardcollection")
    
    def haveparts(self):
        return self.get("~/menu/haveparts")

    def towneventlist(self, check=1):
        return self.get("~/menu/towneventlist", check=check)

    def productlist(self, type="cp"):
        return self.get("~/menu/productlist", type=type)

    def fairy_select(self):
        ret = self.get("~/menu/fairyselect")
        self.remaining_rewards = ret.fairy_select.remaining_rewards
        return ret

    def ranking(self, ranktype_id=0, top=0, move=1):
        return self.get("~/ranking/ranking", ranktype_id=ranktype_id, top=top, move=move)


    def item_use(self, item_id):
        return self.get("~/item/use", item_id=item_id)
    
    def gacha_select(self):
        return self.get("~/gacha/select/getcontents")

    def gacha_buy(self, bulk=1, auto_build=1, product_id=1): #DSjuan: product_id=2, auto_build=0, bulk=0
        return self.get("~/gacha/buy", bulk=bulk, auto_build=auto_build, product_id=product_id)


    def lvup_status(self):
        return self.get("~/town/lvup_status")

    def pointsetting(self, ap, bc):
        return self.get("~/town/pointsetting", ap=ap, bc=bc)

    def card_exchange(self, mode=1):
        return self.get("~/card/exchange", mode=mode)

    def card_compound(self, base_serial_id, add_serial_id):
        if isinstance(add_serial_id, list):
            return ",".join(map(str, add_serial_id))
        return self.get("~/compound/buildup/compound", base_serial_id=base_serial_id, add_serial_id=add_serial_id)

    def card_sell(self, serial_id):
        if isinstance(serial_id, list):
            return ",".join(map(str, serial_id))
        return self.get("~/trunk/sell", serial_id=serial_id)


    def like_user(self, users, dialog=1):
        if isinstance(users, list):
            users = ",".join(map(str, users))
        return self.get("~/friend/like_user", dialog=dialog, users=users)

    def add_friend(self, user_id, dialog=1):
        if isinstance(user_id, list):
            users = ",".join(map(str, user_id))
        return self.get("~/friend/add_friend", user_id=user_id, dialog=dialog)

    def cancel_apply(self, user_id, dialog=1):
        if isinstance(user_id, list):
            users = ",".join(map(str, user_id))
        return self.get("~/friend/cancel_apply", user_id=user_id, dialog=dialog)

    def remove_friend(self, user_id, dialog=1):
        if isinstance(user_id, list):
            users = ",".join(map(str, user_id))
        return self.get("~/friend/remove_friend", user_id=user_id, dialog=dialog)

    def friend_notice(self, move=0):
        return self.get("~/menu/friend_notice", move=move)

    def friend_appstate(self, move=0):
        return self.get("~/menu/friend_appstate", move=move)

    def comment_update(self, greeting="libma"):
        return self.get("~/comment/update", greeting=greeting)

    def comment_send(self, user_id, like_message="libma", comment_id=None):
        if comment_id is None:
            comment_id = self.user_id
        return self.get("~/comment/send", comment_id=comment_id, user_id=user_id, like_message=like_message)


    def save_deck_card(self, cards, leader=None):
        if isinstance(cards, list):
            _cards = []
            for card in cards:
                if isinstance(card, Card):
                    _cards.append(card.serial_id)
                else:
                    _cards.append(card)
            cards = _cards
            while len(cards) < 12:
                cards.append('empty')
            cards = ",".join(map(str, cards))

        if leader is None:
            leader = cards.split(",", 1)[0]
        elif isinstance(leader, Card):
            leader = leader.serial_id

        data = self.get("~/cardselect/savedeckcard", C=cards, lr=leader)
        self.roundtable = [self.cards[int(x)] for x in \
                data.xpath('//deck_cards/text()')[0].split(',') if x != 'empty']
        return data

    def roundtable_edit(self, move=1):
        data = self.get("~/roundtable/edit", move=move)
        self.roundtable = [self.cards[int(x)] for x in \
                data.xpath('//deck_cards/text()')[0].split(',') if x != 'empty']
        return data

    @property
    def cost(self):
        if not getattr(self, 'master_cards', None):
            self.masterdata_card()
        if not getattr(self, 'roundtable', None):
            self.roundtable_edit()
        return sum([x.cost for x in self.roundtable])
    
    def story_getoutline(self, check=1):
        return self.get("~/story/getoutline", check=check)

    def story_battle(self):
        return self.get("~/story/battle")

    def start_scenario(self, scenario_id):
        return self.get("~/scenario/start_scenario", scenario_id=scenario_id)

    def next_scenario(self, phase_id, scenario_id):
        return self.get("~/scenario/next_scenario", phase_id=phase_id, scenario_id=scenario_id)

    def start_eventsc(self, scenario_id):
        return self.get("~/scenario/start_eventsc", scenario_id=scenario_id)

    def next_eventsc(self, scenario_id, phase_id):
        return self.get("~/scenario/next_eventsc", scenario_id=scenario_id, phase_id=phase_id)

    def tutorial_next(self, step=7025):
        return self.get("~/tutorial/next", S=self.session_id, step=step)


    def battle_area(self):
        return self.get("~/battle/area")

    def battle_userlist(self, knight_id=0, move=1, parts_id=0):
        return self.get("~/battle/battle_userlist", knight_id=knight_id, move=move, parts_id=parts_id)

    def battle_battle(self, user_id, lake_id=0, parts_id=0):
        return self.get("~/battle/battle", user_id=user_id, lake_id=lake_id, parts_id=parts_id)


    def area(self):
        return self.get("~/exploration/area")

    def floor(self, area_id):
        return self.get("~/exploration/floor", area_id=area_id)

    def floor_status(self, area_id, floor_id, check=1):
        return self.get("~/exploration/get_floor", area_id=area_id, floor_id=floor_id, check=check)

    def explore(self, area_id, floor_id, auto_build=1):
        '''
        event:
            2 - encounter
            3 - got card
            5 - next floor
            15 - got card and autocomp
        '''
        return self.get("~/exploration/explore", area_id=area_id, floor_id=floor_id, auto_build=auto_build)

    def fairy_floor(self, serial_id, user_id, check=1):
        return self.get("~/exploration/fairy_floor", serial_id=serial_id, user_id=user_id, check=1)

    def fairy_battle(self, serial_id, user_id):
        if time.time() - self.fairy_battle_cooldown < self.FAIRY_BATTLE_COOLDOWN:
            time.sleep(self.FAIRY_BATTLE_COOLDOWN - time.time() + self.fairy_battle_cooldown)
        ret = self.get("~/exploration/fairybattle", serial_id=serial_id, user_id=user_id)
        self.fairy_battle_cooldown = time.time()
        return ret

    def fairy_history(self, serial_id, user_id):
        return self.get("~/exploration/fairyhistory", serial_id=serial_id, user_id=user_id)

    # what for?
    def fairy_lose(self, serial_id, user_id):
        return self.get("~/exploration/fairy_lose", serial_id=serial_id, user_id=user_id)

    # error api?
    def fairy_win(self, serial_id, user_id):
        return self.get("~/exploration/fairy_win", serial_id=serial_id, user_id=user_id)


    def _bind_data(self, phone, nickname, groupid=1):
        return self.post('http://www.niuxba.com/ma/backend/cgi-bin/bindUser.php', data=json.dumps({
            'phone': phone,
            'nickName': nickname,
            'groupId': groupid,
            })).json

    def _get_user_info(self, phone, userid, groupid=1, serverno=6):
        return self.post('http://www.niuxba.com/ma/backend/cgi-bin/getUserInfo.php', data=json.dumps({
            'phone': phone,
            'groupId': groupid,
            'serverNo': serverno,
            'userId': userid,
            })).json

    def _get_card_info(self, phone, userid, groupid=1, serverno=6):
        return self.post('http://www.niuxba.com/ma/backend/cgi-bin/getCardInfo.php', data=json.dumps({
            'phone': phone,
            'groupId': groupid,
            'serverNo': serverno,
            'userId': userid,
            })).json

    def _get_friend_info(self, phone, userid, groupid=1, serverno=6):
        return self.post('http://www.niuxba.com/ma/backend/cgi-bin/getFriendInfo.php', data=json.dumps({
            'phone': phone,
            'groupId': groupid,
            'serverNo': serverno,
            'userId': userid,
            })).json

if __name__ == '__main__':
    ma = MA()
    login = ma.login(config.loginId, config.password)
    import IPython; IPython.embed()
