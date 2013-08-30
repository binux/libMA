#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2013-08-11 13:59:06

import os
from libmproxy import controller, proxy
from CryptUtils import crypt

c = True
class StickyMaster(controller.Master):
    def handle_request(self, msg):
        if ".ma." in msg.get_url():
            path = msg.path.rsplit("?")[0]
            print """
    def %s(%s):
        return self.get(%s)""" % (path.split("/")[-1],
                                  ", ".join(["self", ] + msg.get_form_urlencoded().keys()),
                                  
                                  ", ".join(['"%s"' % path.replace("/connect/app", "~"), ]\
                                          +["%s=%s" % (x, x) for x in msg.get_form_urlencoded().keys()]))

        print msg.get_url()
        if msg.method == 'POST':
            try:
                for key, value in msg.get_form_urlencoded().items():
                    print "\t%s=%s" % (key, crypt.decode64(value))
            except:
                print "\tdecode error!"
        msg.reply()

if __name__ == '__main__':
    config = proxy.ProxyConfig(
        cacert = os.path.expanduser("~/.mitmproxy/mitmproxy-ca.pem")
    )
    server = proxy.ProxyServer(config, 8080)
    m = StickyMaster(server)
    try:
        m.run()
    except KeyboardInterrupt:
        m.shutdown()
