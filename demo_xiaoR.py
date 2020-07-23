#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/9/18 9:55
# @Version : 1.0
# @File    : demo1_core.py
# @Author  : Jingsheng Tang
# @Version : 1.0
# @Contact : mrtang@nudt.edu.cn   mrtang_cs@163.com
# @License : (C) All Rights Reserved

from bci_core import *
from guiengine import *
import multiprocessing
from marker import Marker
from rz_global_clock import global_clock

class bciApp(bciCore):
    def __init__(self):
        super(bciApp,self).__init__(config_path = r'./config.js')

        self.PHASES = [ {'name':'start','next':'test','duration':1},
                        {'name':'test','next':'relax','duration':5},
                        {'name':'relax','next':'test','duration':3},
                        {'name':'rrelax','next':'stop','duration':1}]

        self.CODER = DefaultCoder()

        layout = {'screen': {'size': (1000, 250), 'color': (0, 0, 0), 'type': 'normal',
                             'Fps': 60, 'caption': 'this is an example'},
                  'ssvep1': {'class': 'sinBlock', 'parm': {'size': (150, 150), 'position': (125, 125),
                        'bordercolor':(0,0,0),'anchor':'center','frequency': 6, 'visible': True, 'start': False}},
                  'ssvep2': {'class': 'sinBlock', 'parm': {'size': (150, 150), 'position': (375, 125),
                        'bordercolor':(0,0,0),'anchor': 'center','frequency': 7, 'visible': True, 'start': False}},
                  'ssvep3': {'class': 'sinBlock', 'parm': {'size': (150, 150), 'position': (625, 125),
                        'bordercolor':(0,0,0),'anchor':'center','frequency': 8, 'visible': True, 'start': False}},
                  'ssvep4': {'class': 'sinBlock', 'parm': {'size': (150, 150), 'position': (875, 125),
                        'bordercolor':(0,0,0),'anchor': 'center', 'frequency': 9, 'visible': True, 'start': False}},
                  }

        self.gui = GuiIF(None,layout)
        _ = multiprocessing.Process(target=guiengine_proc,args=(self.gui.args,))
        _.start()
        self.gui.wait()

        sp_ip = self.configs['signal_processing']['sp_host_ip']
        sp_port = self.configs['signal_processing']['sp_host_port']
        self.marker = Marker((sp_ip,sp_port))

        self.TEST_NUM = 80
        self.test_count = 1

    def transition(self,phase):
        write_log(phase)
        if phase == 'test':
            self.gui.update({'ssvep1': {'start': True,'bordercolor':(0,0,0)}, 'ssvep2': {'start': True,'bordercolor':(0,0,0)}, 'ssvep3': {'start': True,'bordercolor':(0,0,0)},
                             'ssvep4': {'start': True,'bordercolor':(0,0,0)}}, {})

            t = global_clock()
            print(t)
            self.marker.send_marker({'process':{'value':[1],'timestamp':[t]}})    #开始测试

        elif phase == 'relax':
            self.gui.update({'ssvep1': {'start': False}, 'ssvep2': {'start': False}, 'ssvep3': {'start': False},
                             'ssvep4': {'start': False}}, {})

            self.marker.send_marker({'process': {'value': [2],'timestamp':[global_clock()]}})  #测试完成

            self.test_count += 1
            if self.test_count > self.TEST_NUM:
                self.change_phase('rrelax')

    def stop_run(self):
        self.gui.quit()

    def process(self,result):
        if result is not None:
            print(result)
            mapp = {'6':'ssvep1','7':'ssvep2','8':'ssvep3','9':'ssvep4'}
            self.gui.update({mapp[str(result)]: {'bordercolor':(255,0,0)}},{})

if __name__ == '__main__':
    app = bciApp()
    app.start_run()


