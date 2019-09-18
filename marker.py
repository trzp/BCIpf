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

class Marker():
    def __init__(self,server_addr):
        self.sc = SyncClient(server_addr)
        self.sc.start_sync()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_addr = server_addr
        self.nCLK = time.clock()
        self._markers_ = {}

    # 为了缓解通信压力，marker发送间隔不低于0.1s
    def send_marker(self,marker):
        # marker: eg. {'mkr1':{'value':[0],'timestamp':[100]},'mkr2':{'value':[1,2],'timestamp':[200,250]}}
        # 更新marker
        for key in marker:
            marker[key]['timestamp'] = list(map(self.sc.convert2remoteCLK,marker[key]['timestamp']))    # 时钟校准
            mkr = marker[key]
            if key in self._markers_:
                self._markers_[key]['value'].extend(mkr['value'])
                self._markers_[key]['timestamp'].extend(mkr['timestamp'])
            else:
                self._markers_[key] = mkr

        clk = time.clock()
        if clk - self.nCLK >= 0.1:
            buf = json.dumps(self._markers_)
            buf = bytes(buf,encoding='utf-8')
            self.sock.sendto(buf,self.server_addr)
            self._markers_ = {}
            self.nCLK = clk







