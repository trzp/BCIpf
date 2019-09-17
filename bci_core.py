#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn

from __future__ import division
from __future__ import print_function
from phase import *
import threading
# from rz_global_clock import global_clock as sysclock
from rz_clock import clock as sysclock
import time
from coder import DefaultCoder
import json
import socket


class bciCore(threading.Thread):

    def __init__(self,config_path = r'./config.js'):
        self.PHASES = []
        self.current_phase = 'start'
        self.__nreload = False
        self.__pinterval = 0.1
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self._phIF = None
        self.CODER = DefaultCoder()

        with open(config_path, 'r') as f:
            self.configs = json.load(f)

    def process(self,result):#在子类中实现,子类如果重载process，将不会修改self.__nreload值,子线程将自动结束
        self.__nreload = True

    def transition(self,phase): #在子类中实现
        pass

    def change_phase(self,phase):
        self._phIF.change_phase(phase)
    
    def write_log(self,m):
        print('[bciCore][%.4f]%s'%(sysclock(),m))

    def __mainloop(self): #主线程接受phase驱动整个程
        self.write_log('program started!')
        self.start()    #启动子线程
        while True:
            self.current_phase = self._phIF.next_phase()
            self.transition(self.current_phase)
            if self.current_phase == 'stop':        # stop phase
                break
                
        self.stop_run()
        self.write_log('[bciCore] program ended!')
        time.sleep(1)

    def run(self):  #异步子线程,按照fps定义的节奏定时执行
        if self.__nreload: return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 建立udp socket
        addr = self.configs['signal_processing']['result receiver address'][0]  # 绑定到0号地址
        sock.bind(tuple(addr))
        sock.setblocking(False)
        clk = sysclock()
        while True:
            c = sysclock()
            if c - clk >= self.__pinterval:
                res = None
                try:
                    buf,addr = sock.recvfrom(1024)
                    res = self.CODER.decode(buf)
                except socket.error:
                    pass

                self.process(res)
                clk += self.__pinterval
            time.sleep(0.05)

    def start_run(self): #mainloop
        self._phIF = phaseInterface(self.PHASES)
        ph_proc = multiprocessing.Process(target = phase_process,args = self._phIF.args)
        ph_proc.start()
        self.__mainloop()
        
    def stop_run(self):
        pass

class bciApp(bciCore):
    def __init__(self):
        bciCore.__init__(self,config_path = r'./config.js')
        self.PHASES = [ {'name':'start','next':'prompt','duration':1},
                        {'name':'prompt','next':'que'},
                        {'name':'que','next':'stop','duration':4}]
        self.CODER = DefaultCoder()

    def transition(self,phase):
        self.write_log(phase)

    def process(self,result):
        if self.current_phase == 'prompt':
            time.sleep(1)
            self.change_phase('que')

if __name__ == '__main__':
    app = bciApp()
    app.start_run()