#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/8/26 19:11
# @Version : 1.0
# @File    : sync_sock.py
# @Author  : Jingsheng Tang
# @Version : 1.0
# @Contact : mrtang@nudt.edu.cn   mrtang_cs@163.com
# @License : (C) All Rights Reserved


import sys
import socket
from rz_global_clock import global_clock
import struct
import time
import numpy as np
import uuid
import sys

# 打印进度条
def show_progress(num,full,width=50):
    if num >= full:
        num = full
    show_str = ('[sync_sock][connect to server] %%-%ds' % width) % (int(width * num / full) * ">")
    print('\r%s %d/%i'%(show_str, num, full),end='')

def get_mac_address():
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:] 
    return ":".join([mac[e:e+2] for e in range(0,11,2)])

class SyncServer():
    def __init__(self,addr):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.bind(addr)
        self.sock.listen(10)
        self.mac_addr = get_mac_address()
        self.count = 0
        print('[sync_sock module] ready for remote clock synchronize')

    def start(self):
        self.count += 1
        self.client, addr = self.sock.accept()
        print('[sync_sock module] start clock synchronize with',addr)
        request = bytes.decode(self.client.recv(128),encoding='utf-8')   # request: sync-request:macaddr
        if request[:13] == 'sync-request:':
            if self.mac_addr == request[13:]:   #匹配
                self.client.send(bytes('sync-mac-match',encoding='utf-8'))
                self.client.close()
                #self.sock.close()
            else:
                self.client.send(bytes('sync-ready',encoding='utf-8'))
                self.syncclock()
                self.client.close()
                #self.sock.close()
        else:
            self.client.send(bytes('unrecognized request',encoding='utf-8'))

        print('[sync_sock module] clock synchronize complete')

    def syncclock(self):
        while True:
            buf = self.client.recv(128)
            try:
                request = bytes.decode(buf, encoding = 'utf-8')
                if request[:7] == 'sync-ok':
                    return
            except:
                pass

            clock_buf = struct.pack('d',global_clock())
            self.client.send(clock_buf)

class SyncClient():
    def __init__(self,server_addr):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connect = False

        for i in range(31):
            try:
                show_progress(i,30,30)
                self.sock.connect(server_addr)
                connect = True
                show_progress(30, 30, 30)
                print('\n')
                break
            except socket.error:
                time.sleep(2)

        if not connect:
            raise socket.error('[sync_sock module] can not connect to the remote server. please check connection')

        self.mac_addr = get_mac_address()
        self.er = None

    def convert2remoteCLK(self,clk):
        return clk + self.er

    def start_sync(self):
        '''
        return clocks' error
        client's clock + er = server's clock
        '''
        print('[sync_sock] start clock synchronize with remote server')
        self.sock.send(bytes('sync-request:%s'%(self.mac_addr),encoding='utf-8'))
        reply = bytes.decode(self.sock.recv(128),encoding='utf-8')
        if reply[:14] == 'sync-mac-match':
            self.er = 0
            self.sock.close()
            print('[sync_sock] finished clock synchronize. clock offset: %d seconds'%(self.er))
            return 0
        elif reply[:10] == 'sync-ready':
            self.er = self.syncclock()
            self.sock.send(bytes('sync-ok',encoding='utf-8'))
            self.sock.close()
            print('[sync_sock] finished clock synchronize. clock offset: %d seconds'%(self.er))
            return self.er
        else:
            raise Exception('commands error %s'%(reply))


    def syncclock(self):
        record = np.zeros((20,4))
        for i in range(20):
            clkA = global_clock()
            clk_buf = struct.pack('d', clkA)
            self.sock.send(clk_buf)
            reply = self.sock.recv(128)
            clkB = global_clock()
            clk_server = struct.unpack('d',reply)[0]
            t = 0.5*(clkB - clkA)
            record[i,:] = np.array([t,clkA,clkB,clk_server])
            time.sleep(0.2)

        # 取通信时间最短的一组计算参数
        ind = np.argsort(record[:,0])[0]
        t,clkA,clkB,clk_server = record[ind,:]
        er = clk_server - t - clkA
        print(er)
        return er

def sync_proc(addr):
    ser = SyncServer(addr)
    for i in range(10):
        ser.start()


# eg.
if __name__ == '__main__':
    addr = (sys.argv[1],int(sys.argv[2]))
    sync_proc(addr)












