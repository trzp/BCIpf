#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn


import os,sys
rootpath = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(rootpath + '\\amplifiers')

import threading

from rz_global_clock import global_clock
import socket
import thread
import subprocess
from storage import *



class SigPro(threading.Thread):
    def __init__(self,config_path = r'./config.js'):
        with open(config_path,'r') as f:
            self.config = json.load(f)
        
        self.configs = self.config['signal_processing']
        exec('from %s import EEGamp'%(self.configs['amplifier']))

        # 不需要接受marker则不启动marker子线程
        if self.configs['sp_host_ip'] is None:
            self.__marker_thread_on = False
        else:
            self.__marker_thread_on = True
            addr = (self.configs['sp_host_ip'],self.configs['sp_host_port'])

            #启用临时进程进行时钟同步
            subprocess.Popen('python sync_sock.py %s %i' % (self.configs['sp_host_ip'], self.configs['sp_host_port']))

            self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # 建立udp socket
            self.sock.bind(addr)

        self.output_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # 建立udp socket
        self.output_addr = self.configs['result receiver address']

        self.amp = EEGamp(self.configs['samplingrate'],self.configs['eeg channels'],self.configs['eeg channel label'],
                          self.configs['ref channels'],self.configs['ref channel label'])


        threading.Thread.__init__(self)
        self.setDaemon(True)  # 子线程用于接受trigger 并且子线程随主线程一起结束
        self._lock = thread.allocate_lock()

        self.__marker = {}
        self.output_buffer = ""

        # 数据保存模块初始化
        self.stIF = StorageInterface()
        self.storage_proc = multiprocessing.Process(target=storage_pro, args=(stIF.args, config))

    def run(self): # 子线程，记录marker
        samplingrate = self.configs['samplingrate']
        while self.__marker_thread_on:
            buf,addr = self.sock.recvfrom(512)
            marker = json.loads(buf) # eg. marker: {'mkr1':{'value':[1],'timestamp':[xxxx]}}

            self._lock.acquire()
            for key in marker:
                marker[key]['timepoint'] = [int((x - self.start_clk) * samplingrate) for x in marker[key]['timestamp']]

                if key in self.__marker:
                    self.__marker[key]['value'].extend(marker[key]['value'])
                    self.__marker[key]['timepoint'].extend(marker[key]['timepoint'])
                else:
                    self.__marker[key] = {'value':marker[key]['value'],'timepoint':marker[key]['timepoint']}
            self._lock.release()

    def process(self,eeg,marker):
        '''
        return value: 0 doing nothing
                      1 send result through the framework, to result should be transform to string bufffer and
                      put in to the self.output_buffer
                      -1 end the program
                      ps: the predefined marker named 'endprocess' can end the program within the framework
        '''
        if len(marker)>0:
            print(marker)
        return 0

    def start_run(self):
        # 启动数据保存进程
        self.storage_proc.start()
        self.start()  # 启动子线程,接收marker

        self.start_clk = global_clock()
        lsclk = self.start_clk - 0.1  #确保立即采集数据，采集数据与start_clk对齐

        while True:
            clk = global_clock()
            if clk - lsclk >= 0.1:
                eeg = self.amp.read()
                marker = copy(self.__marker)
                self.__marker = {}
                self.stIF.write_eeg_to_file(eeg)
                self.stIF.write_mkr_to_file(marker)
                r = self.process(eeg,marker)
                if r == 1:
                    [self.output_sock.sendto(self.output_buffer,addr) for addr in self.output_addr]
                elif r == -1:
                    self.stIF.close()
                    break
                else:
                    pass
                lsclk += 0.1
            time.sleep(0.05)

        print('[sig pro] process ended!')


def main():
    args = sys.argv
    if len(args)>1:
        configs = args[1]
        s = SigPro(configs)
        s.start_run()
    else:
        s = SigPro()
        s.start_run()

if __name__ == '__main__':
    main()



