#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn


import numpy as np
import math
#from rz_global_clock import global_clock

class EEGamp(object):
    def __init__(self,samplingrate,eegchannels,channelnames=[],refchannels=[],refchannellabel=[],readstep = 0.1):
        self.samplingrate = samplingrate
        sin_f = 8.                                     #系统默认产生8Hz的正弦波
        x = np.arange(0,1/sin_f,1./samplingrate)
        y = np.sin(2*np.pi*sin_f*x).astype(np.float64)
        rpt = int(math.ceil(readstep*sin_f))
        self.y = np.asmatrix(np.hstack([y]*rpt))      #确保y的长度大于readstep
        tem = np.repeat(self.y,len(eegchannels),0)
        self.y = np.array(tem)
        self.readpoint = int(readstep * samplingrate)

    def read(self):
        data = self.y[:,:self.readpoint]
        self.y = np.hstack((self.y[:,self.readpoint:],data))
        # return global_clock(),data
        return data

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    eegamp = EEGamp(128,[1,2])
    data = eegamp.read()
    for i in range(5):
        buf = eegamp.read()
        data = np.hstack((data,buf))

    plt.plot(range(data.shape[-1]),data[1,:])
    plt.show()
    