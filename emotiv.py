#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/9/19 9:59
# @Version : 1.0
# @File    : bpamp.py
# @Author  : Jingsheng Tang
# @Version : 1.0
# @self.contact : mrtang@nudt.edu.cn   mrtang_cs@163.com
# @License : (C) All Rights Reserved

# 修改来自bp的RDA demo

import socket
from RDAbymrtang import *
import threading
from rz_global_clock import global_clock
import _thread
import time
import numpy as np

# 配置示例
# 注意:由于是实时获取设备的数据，因此，并不能保证每次read都能返回等量的数据。但并不影响结果。

'''
"signal_processing":
    {
       "eeg channels": [1,2,3,4,5,6,7,8,9,10,11,12,13,4,15,16],
       "samplingrate": 128,
       "amplifier": "emotiv",
       "amplifier params":{'remote device ip':'127.0.0.1','remote device port':55123}
    }
'''

# 不同bp产品型号对应不同的信号发送间隔
BPINTERVAL = {'epoc+':0.050,}

class EEGamp():
    def __init__(self,samplingrate,eegchannels = range(16),readstep = 0.1,**kwargs):
        threading.Thread.__init__(self)
        ip = kwargs['remote device ip']
        port = kwargs['remote device port']  #55123
        if kwargs['product model'] not in BPINTERVAL:
            raise SystemError('currently only %s supported, please contact mrtang_cs@163'%(str(BPINTERVAL.keys())[10:-1]))

        self.addr = (ip,port)
        
        if samplingrate != 128 or len(eegchannels) != 16:
            raise SystemError('some parameters error: samplingrate is not 128 ? eegchannels is not 16 ?')

        self.DATA = []
        self.CLKS = []
        self.finish = False
        self._lock = threading.Lock()
        thread2 = threading.Thread(target = self.thread_fun,args=(),daemon=True)
        thread2.start()
        
        print('[emotiv] device ready')

    def close(self):
        self.finish = True

    def __del__(self):
        self.close()

    def read(self):
        if len(self.DATA) == 0:
            return None,None

        try:
            eeg = np.vstack(self.DATA)
            self.DATA = []
            clk = self.CLKS[0]
            self.CLKS = []
        except:
            pass
        return eeg.transpose(),clk

    def thread_fun(self):  # 开启后始终将数据缓存到self.DATA中
        self.con =  socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.con.bind(self.addr)
        
        while not self.finish:
            buf,addr = self.con.recvfrom(51200)
            buf = bytes.decode(buf, encoding = 'utf-8')
            dd = buf.split('*=*')
            self._lock.acquire()
            for dt in dd:
                if len(dt)>0:
                    d = [float(item) for item in dt.split(',')]
                    self.CLKS.append(d[0])
                    self.DATA.append(np.array(d[3:],dtype=np.float32))
            self._lock.release()

if __name__ == '__main__':
    amp = EEGamp(128,**{'remote device ip':'127.0.0.1','remote device port':65123,'product model':'epoc+'})
    tem = []
    while True:
        eeg,clk = amp.read()
        time.sleep(0.1)
