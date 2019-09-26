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
       "eeg channels": [1, 2, 3, 4],
       "samplingrate": 100,
       "amplifier": "bpamp",
       "amplifier params":{'remote device ip':'localhost','remote device port':51244}
    }
'''

# 不同bp产品型号对应不同的信号发送间隔
BPINTERVAL = {'actichamp':0.050,
              'brainamp':0.020}

class EEGamp(threading.Thread):
    def __init__(self,samplingrate,eegchannels,readstep = 0.1,**kwargs):
        threading.Thread.__init__(self)
        ip = kwargs['remote device ip']
        port = kwargs['remote device port']  #51244
        if kwargs['product model'] not in BPINTERVAL:
            raise SystemError('currently only %s supported, please contact mrtang_cs@163'%(str(BPINTERVAL.keys())[10:-1]))
        
        self.interval = BPINTERVAL[kwargs['product model']]
        
        
        addr = (ip,port)
        self.con =  socket.socket(socket.AF_INET,socket.SOCK_STREAM)

        connect = False
        for i in range(30):
            print('\r[bp amp] connecting >>'+ '>>'*i,end='')
            try:
                self.con.connect(addr)
                connect = True
                break
            except:
                time.sleep(1)

        print('\n')
        if not connect: raise SystemError('can not connect to the BP amplifier')

        self.eegchs = eegchannels
        self.eegchNum = len(self.eegchs)
        self.fs = samplingrate
        self.DATA = []
        self.CLKS = []
        self._lock = _thread.allocate_lock()
        self.deviceOK = False
        self.finish = False
        self.setDaemon(True)
        self.start()
        while len(self.DATA)< 4:
            time.sleep(0.1)
        self.firstRead = True
        print('[bp amp] device ready')

    def close(self):
        self.finish = True

    def __del__(self):
        self.close()

    def read(self): # 注意，读取0.1秒的数据，也就是两个数据包
        if len(self.DATA) == 0:
            return None,None

        eeg = np.hstack(self.DATA)
        self.DATA = []
        clk = self.CLKS[0]
        self.CLKS = []
        eeg = eeg.reshape(int(eeg.size / self.eegchNum), self.eegchNum).transpose()
        return eeg,clk

    def run(self):  # 开启后始终将数据缓存到self.DATA中
        lastBlock = -1
        while not self.finish:
            # Get message header as raw array of chars
            rawhdr = RecvData(self.con, 24)
            # Split array into usefull information id1 to id4 are self.constants
            (id1, id2, id3, id4, msgsize, msgtype) = unpack('<llllLL', rawhdr)
            # Get data part of message, which is of variable size
            rawdata = RecvData(self.con, msgsize - 24)
            # Perform action dependend on the message type
            if msgtype == 1:
                # Start message, extract eeg properties and display them
                (channelCount, samplingInterval, resolutions, channelNames) = GetProperties(rawdata)
                # reset block counter
                lastBlock = -1

                if len(self.eegchs) != channelCount:
                    raise SystemError('[bp amp] eeg channels is not match between configuration and device setting. configs: %d  device: %d'%(len(self.eegchs),channelCount))

            elif msgtype == 4:
                # Data message, extract data and markers
                clk = global_clock() - self.interval # 数据是50ms范围内的数据，因此受到数据的前0.05s才是数据起始时刻
                (block, points, markerCount, data, markers) = GetData(rawdata, channelCount)
                if not self.deviceOK:
                    fs = points/self.interval
                    if fs != self.fs:
                        raise SystemError('[bp amp] samplingrate is not match between configuration and device setting. configs: %d  device: %d' % (self.fs, fs))
                    self.deviceOK = True

                # Check for overflow
                if lastBlock != -1 and block > lastBlock + 1:
                    print('[bp amp] warning: Overflow with' + str(block - lastBlock) + " datablocks")
                lastBlock = block

                self._lock.acquire()
                self.DATA.append(np.array(data).astype(np.float32))
                self.CLKS.append(clk)
                self._lock.release()

            elif msgtype == 3:
                self.finish = True

        self.con.close()

if __name__ == '__main__':
    amp = EEGamp(200,['ch1','ch2','ch3','ch4'],0.1,**{'remote device ip':'localhost','remote device port':51244})
    while True:
        eeg,clk = amp.read()
        print(eeg.shape,clk)
        time.sleep(0.1)
