#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-05 23:58:01

import config
import requests
from lxml import etree
from urlparse import urljoin
from HttpUtils import _cryptParams
from CryptUtils import crypt

class HeaderError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __repr__(self):
        return '<Error%d>%s' % (self.code, self.message)

    def __str__(self):
        return self.__repr__()

class Card:
    @classmethod
    def from_xml(cls, card):
        c = cls()
        for node in card:
            setattr(c, node.tag, int(node.text))
        return c

    def __init__(self):
        pass

class MA:
    default_http_header = {
            'User-Agent': config.USER_AGENT,
            'Accept-Encoding': 'gzip, deflate',
            }
    HOME = 'connect/app'
    BASE_URL = config.BASE_URL

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.default_http_header)
        self.session_id = None
        self.your_data = {}

    @property
    def islogin(self):
        return bool(self.session_id)

    def abs_path(self, path):
        if path.startswith('~'):
            path = path.replace('~', self.HOME)
        return urljoin(self.BASE_URL, path)

    def cat(self, resource, params={}, **kwargs):
        params.update(kwargs)
        params = _cryptParams(params)
        response = self.session.post(self.abs_path(resource), params)
        return response.content

    def parse_header(self, header):
        error_code = int(header.xpath('./error/code/text()')[0])
        if error_code:
            raise HeaderError(error_code, header.xpath('./error/message/text()')[0])

        your_data = header.xpath('./your_data')
        if your_data:
            your_data = your_data[0]

            for attr in ('name', 'leader_serial_id/i', 'town_level/i', 'percentage/i',
                         'cp/i', 'max_card_num/i', 'free_ap_bc_point/i',
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

            self.ap = int(your_data.xpath('./ap/current/text()')[0])
            self.ap_max = int(your_data.xpath('./ap/max/text()')[0])
            self.ap_interval_time = int(your_data.xpath('./ap/interval_time/text()')[0])
            self.bc = int(your_data.xpath('./bc/current/text()')[0])
            self.bc_max = int(your_data.xpath('./bc/max/text()')[0])
            self.bc_interval_time = int(your_data.xpath('./bc/interval_time/text()')[0])

            if your_data.xpath('./owner_card_list'):
                self.cards = []
                for card in your_data.xpath('./owner_card_list/user_card'):
                    self.cards.append(Card.from_xml(card))
            if your_data.xpath('./itemlist'):
                self.iterms = {}
                for item in your_data.xpath('./itemlist'):
                    self.iterms[item.xpath('./item_id/text()')[0]] = int(item.xpath('./num/text()')[0])

    @property
    def level(self):
        return self.town_level

    def get(self, resource, params={}, **kwargs):
        params.update(kwargs)
        xml = etree.fromstring(crypt.decode(self.cat(resource, params=params)))

        self.parse_header(xml.xpath('/response/header')[0])

        return xml.xpath('/response/body')[0]

    LOGIN_PATH="~/login"
    def login(self, login_id, password):
        body = self.get(self.LOGIN_PATH, login_id=login_id, password=password)
        self.user_id = body.xpath('./login/user_id/text()')[0]
        return body

if __name__ == '__main__':
    ma = MA()
    a = ma.login(config.loginId, config.password)
    import IPython; IPython.embed()
