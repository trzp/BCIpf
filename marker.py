#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/9/11 15:37
# @Version : 1.0
# @File    : marker.py
# @Author  : Jingsheng Tang
# @Version : 1.0
# @Contact : mrtang@nudt.edu.cn   mrtang_cs@163.com
# @License : (C) All Rights Reserved


from sync_sock import SyncClient
import socket
import json
import time
from rz_global_clock import global_clock

class Marker():
    def __init__(self,server_addr):
        self.sc = SyncClient(server_addr)
        self.sc.start_sync()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_addr = server_addr

    def send_marker(self,marker):
        # marker: eg. {'marker1':{'value':[1],'timestamp':[x]},'marker2':{'value':[0],'timestamp':[x]}}
        for mk in marker:
            marker[mk]['timestamp'] = map(self.sc.convert2remoteCLK,marker[mk]['timestamp'])

        buf = json.dumps(marker)
        self.sock.sendto(buf,self.server_addr)

def main():
    with open(r'./config.js', 'r') as f:
        config = json.load(f)

    config = config['signal_processing']
    addr = (config['sp_host_ip'],config['sp_host_port'])
    mk = Marker(addr)
    for i in range(30):
        ts = global_clock()
        mkr = {'mkr1':{'value':[0],'timestamp':[ts]},'mkr2':{'value':[1],'timestamp':[ts]}}
        mk.send_marker(mkr)
        time.sleep(1)
        print 'o'

if __name__ == '__main__':
    main()







