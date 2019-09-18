#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/9/18 16:55
# @Version : 1.0
# @File    : storage2.py
# @Author  : Jingsheng Tang
# @Version : 1.0
# @Contact : mrtang@nudt.edu.cn   mrtang_cs@163.com
# @License : (C) All Rights Reserved

from storage import *
import threading
import socket


u'''
   增加线程通过socket监听远程指令决定模块的状态
'''

class Storage2(Storage,threading.Thread):
    def __init__(self,configs):
        Storage.__init__(self,configs)
        threading.Thread.__init__(self)
        ip = configs['sp_host_ip']
        port = configs['sp_host_port1']
        self.addr = (ip,port)
        self.sub_thread_on = True
        self.setDaemon(True)
        self.start()

    def run(self):
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.bind(self.addr)
        sock.listen(10)
        while self.sub_thread_on:
            server,_ = sock.accept()
            while True:
                try:
                    buf = bytes.decode(server.recv(128),encoding='utf-8')
                    if buf == 'new-trial':
                        self.prefile()  # 完成初始化，storage对象的write_eeg,write_marker可用
                    elif buf == 'trial-end':
                        self.OK = False
                        server.close()
                        break
                    else:
                        raise Exception('[storage server] unrecognized remote command: %s'%(buf))
                except socket.error:    #连接中断,停止保存数据
                    self.OK = False
                    server.close()
                    break


class StorageInterface2():
    def __init__(self):
        self.ev = Event()
        self.que = Queue()
        self.args = {'ev':self.ev,'que':self.que}

    def write_eeg_to_file(self,eeg):
        '''
        eeg:  ch x N
        '''
        self.que.put(['eeg',eeg])

    def write_mkr_to_file(self,mkr):
        if len(mkr)>0:
            self.que.put(['mkr',mkr])

    def close(self):
        self.que.put(['end',''])
        self.ev.set()

    def __del__(self):
        self.que.put(['end', ''])
        self.ev.set()

def storage_pro2(args,configs):
    ev = args['ev']
    que = args['que']
    st = Storage2(configs)

    while not ev.is_set():
        flg,buf = que.get()
        if flg == 'eeg':
            st.write_eeg(buf)
        elif flg == 'mkr':
            st.write_marker(buf)
        else:
            pass
    st.sub_thread_on = False
    print('[storage module] process exit')

class RemoteStorageCmd():
    def __init__(self,configs):
        ip = configs['sp_host_ip']
        port = configs['sp_host_port1']
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip,port))

    def storage_start(self):
        cmd = bytes('new-trial',encoding='utf-8')
        self.sock.send(cmd)

    def storage_exit(self):
        cmd = bytes('trial-end', encoding='utf-8')
        self.sock.send(cmd)

    def close(self):
        self.sock.close()

    def __del__(self):
        self.sock.close()









