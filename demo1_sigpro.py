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

class SigProApp(SigPro):
    def __init__(self, configs_path='./config.js'):
        super(SigProApp, self).__init__(configs_path)
        self.CODER = DefaultCoder()

    def process(self, eeg, marker):
        if len(marker)>0:
            print(marker)
        self.RESULT = 1
        return 1


def main():
    sp = SigProApp()
    sp.start_run()

if __name__ == '__main__':
    main()


