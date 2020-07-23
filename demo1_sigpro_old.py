#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/9/18 9:52
# @Version : 1.0
# @File    : demo1_sigpro.py
# @Author  : Jingsheng Tang
# @Version : 1.0
# @Contact : mrtang@nudt.edu.cn   mrtang_cs@163.com
# @License : (C) All Rights Reserved

from sigpro import SigPro
from sigpro import DefaultCoder
from scipy import signal as scipy_signal
import json
from cca import *
import time


class SigProApp(SigPro):
    def __init__(self, configs_path='./config.js'):
        super(SigProApp, self).__init__(configs_path)
        self.CODER = DefaultCoder()
        
        self.data = []
        self.accdata = False
        self.calres = False
        
        with open(configs_path,'r') as f:
            self.configs = json.loads(f.read())

        Fs = self.configs['signal_processing']['samplingrate']
        fs = Fs / 2
        Wp = [5 / fs, 45 / fs]
        Ws = [3 / fs, 48 / fs]
        [N, Wn] = scipy_signal.cheb1ord(Wp, Ws, 4, 20)
        [self.f_b, self.f_a] = scipy_signal.cheby1(N, 0.5, Wn, btype='bandpass')

        self.ff = [8, 9, 11, 12]
        t = np.arange(0, 20, 1. / Fs)
        self.sx = []
        for f in self.ff:
            x1 = np.mat(np.sin(2 * np.pi * f * t))
            x2 = np.mat(np.cos(2 * np.pi * f * t))
            x3 = np.mat(np.sin(4 * np.pi * f * t))
            x4 = np.mat(np.cos(4 * np.pi * f * t))
            x = np.vstack([x1, x2, x3, x4])
            self.sx.append(x)

    def process(self, eeg, marker):
        if len(marker)>0:
            print(marker)
            if marker['process']['value'][0] == 1:
                self.accdata = True
            elif marker['process']['value'][0] == 2:
                self.calres = True
                self.accdata = False
            else:
                pass

        if self.accdata:
            self.data.append(eeg)
        if self.calres:
            fff = time.clock()
            if len(self.data) == 0:
                return 0

            dd = np.hstack(self.data)
            datafilt = scipy_signal.filtfilt(self.f_b, self.f_a, dd) #滤波处理
            ll = datafilt.shape[1]
            relate = []
            for x in self.sx:
                a,b,r = cca(x[:,:ll],datafilt)
                relate.append(np.max(r))
            indx = np.argmax(relate)
            self.RESULT = self.ff[indx]
            print(self.RESULT)
            self.data = []
            self.calres = False
            print(time.clock()-fff,'??')
            return 1
        return 0

def main():
    sp = SigProApp()
    sp.start_run()

if __name__ == '__main__':
    main()


