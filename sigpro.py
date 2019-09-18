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
import _thread as thread
import subprocess
from storage2 import *
from coder import DefaultCoder


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
        self.RESULT = ""

        # 数据保存模块初始化
        self.SAVEDATA = False
        if self.configs['save data']: self.SAVEDATA = True
        if self.SAVEDATA:
            self.stIF = StorageInterface()
            self.storage_proc = multiprocessing.Process(target=storage_pro, args=(self.stIF.args, self.configs))
        
        # 发送结果的编码器
        self.CODER = DefaultCoder()

    def run(self): # 子线程，记录marker
        samplingrate = self.configs['samplingrate']
        while self.__marker_thread_on:
            buf,addr = self.sock.recvfrom(512)
            buf = bytes.decode(buf,encoding='utf-8')
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
                      put in to the self.RESULT
                      -1 end the program
                      ps: the predefined marker named 'endprocess' can end the program within the framework
        '''
        return 0

    def start_run(self):
        if self.SAVEDATA: self.storage_proc.start()
        self.start()  # 启动子线程,接收marker
        print('[sigpro module] process started')
        self.start_clk = global_clock()
        print(self.start_clk,'startclock')
        lsclk = self.start_clk - 0.1  #确保立即采集数据，采集数据与start_clk对齐

        while True:
            clk = global_clock()
            if clk - lsclk >= 0.1:
                eeg = self.amp.read()
                marker = copy(self.__marker)
                self.__marker = {}
                if self.SAVEDATA:
                    self.stIF.write_eeg_to_file(eeg)
                    self.stIF.write_mkr_to_file(marker)
                r = self.process(eeg,marker)
                if r == 1:
                    [self.output_sock.sendto(self.CODER.encode(self.RESULT),tuple(addr)) for addr in self.output_addr]
                elif r == -1:
                    if self.SAVEDATA:
                        self.stIF.close()
                    break
                else:
                    pass
                lsclk += 0.1
            time.sleep(0.05)

        print('[sigpro module] process exit')


class SigProApp(SigPro):
    def __init__(self,configs_path = './config.js'):
        super(SigProApp,self).__init__(configs_path)
        self.CODER = DefaultCoder()
    
    def process(self,eeg,marker):
        # if len(marker)>0:
        #     print(marker)
        return 0
        
def main():
    sp = SigProApp()
    sp.start_run()

if __name__ == '__main__':
    main()



