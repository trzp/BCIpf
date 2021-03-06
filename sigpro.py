#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn


import os,sys
rootpath = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(rootpath + '\\amplifiers')

import threading
import _thread as thread
import subprocess
from storage2 import *
from coder import DefaultCoder
from rz_clock import clock


# logging: 2019/9/29
# 改进建议：将process返回以及保存的数据，直接提供原始的时间戳。避免写入start_clk带来的麻烦


class SigPro():
    def __init__(self,config_path = r'./config.js'):
        with open(config_path,'r') as f:
            buf = f.read()
            self.config = json.loads(buf)

        self.spconfig = self.config['signal_processing']

        # 不需要接受marker则不启动marker子线程
        if self.spconfig['sp_host_ip'] is None:
            self.__marker_thread_on = False
        else:
            self.__marker_thread_on = True
            addr = (self.spconfig['sp_host_ip'],self.spconfig['sp_host_port'])

            #启用临时进程进行时钟同步
            #客户端进程完成同步获得计算同步参数，以本机时钟为准。因此该进程无需关注是否完成同步
            subprocess.Popen('python sync_sock.py %s %i' % (self.spconfig['sp_host_ip'], self.spconfig['sp_host_port']))
            time.sleep(0.1)

            # sock用于接受marker
            self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # 建立udp socket
            self.sock.bind(addr)

        #用于发送结果
        self.output_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # 建立udp socket
        self.output_addr = self.spconfig['result receiver address']

        #放大器模块导入
        ampclass = {}
        exec('from %s import EEGamp' % (self.spconfig['amplifier'],),ampclass) # python3 对exec进行了安全性升级，注意参数的使用
        EEGamp = ampclass['EEGamp']
        self.amp = EEGamp(self.spconfig['samplingrate'],self.spconfig['eeg channels'],0.1,**self.spconfig['amplifier params'])

        self.__marker = {}
        self.RESULT = ""
        self.start_record = False # 用于主线程和marker线程同步，解决start_clk未初始化
        
        # 发送结果的编码器
        self.CODER = DefaultCoder()
        
        # 数据保存模块初始化
        self.stIF = StorageInterface()
        self.storage_proc = multiprocessing.Process(target=storage_pro, args=(self.stIF.args, self.spconfig))
        self.storage_proc.start()
        self.stIF.wait()

        self._lock = thread.allocate_lock()
        self.marker_thread = threading.Thread(target = self.thread_fun,args = (),daemon=True)
        
        self.running = True

    def thread_fun(self): # 子线程，记录marker
        samplingrate = self.spconfig['samplingrate']
        while not self.start_record:
            pass

        while self.__marker_thread_on:
            buf,addr = self.sock.recvfrom(512)
            buf = bytes.decode(buf,encoding='utf-8')
            marker = json.loads(buf) # eg. marker: {'mkr1':{'value':[1],'timestamp':[xxxx]}}

            self._lock.acquire()
            for key in marker:
                if key == 'endsigpro':
                    self.__marker_thread_on = False
                    self.running = False
                    break
            
                marker[key]['timepoint'] = [int((x - self.start_clk) * samplingrate) for x in marker[key]['timestamp']]
                
                if key == 'new-record':
                    self.stIF.new_record()
                elif key == 'end-record':
                    self.stIF.end_record()
                else:
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
                      ps: the predefined marker named 'endsigpro' can end the program within the framework
        '''
        return 0

    def ac_once(self,first=False):
        if first:
            while True:
                eeg,clk = self.amp.read()
                if eeg is not None:
                    break
                time.sleep(0.01)
        else:
            eeg, clk = self.amp.read()

        marker = copy(self.__marker)
        self.__marker = {}
        # if self.SAVEDATA:
        self.stIF.write_eeg_to_file(eeg)
        self.stIF.write_mkr_to_file(marker)
        r = self.process(eeg, marker)
        return r,clk

    def start_run(self):
        self.marker_thread.start()  # 启动子线程,接收marker
        print('[sigpro module] process started')

        r,self.start_clk = self.ac_once(first=True)
        self.start_record = True  #告知子线程，启动了数据采集

        lsclk = clock()
        while self.running:
            clk = clock()
            if clk - lsclk >= 0.1:
                r,_ = self.ac_once(first=False)
                if r == 1:
                    [self.output_sock.sendto(self.CODER.encode(self.RESULT),tuple(addr)) for addr in self.output_addr]
                elif r == -1:
                    break
                else:
                    pass
                lsclk += 0.1
            time.sleep(0.05)

        self.amp.close()
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



