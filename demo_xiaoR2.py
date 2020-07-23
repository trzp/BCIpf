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

import win32api,win32con

from wifirobot_ctrl import WIFIROBOT_CTR

cmdss = [['forward',2],['left',2],['rleft',1.4],['backward',1],['right',2],['rright',1.4]]

class bciApp(bciCore):
    def __init__(self):
        super(bciApp,self).__init__(config_path = r'./config.js')

        self.PHASES = [ {'name':'start','next':'test','duration':1},
                        {'name':'test','next':'relax','duration':7},
                        {'name':'relax','next':'test','duration':5},
                        {'name':'rrelax','next':'stop','duration':1}]

        self.CODER = DefaultCoder()
        
        w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        
        camera_h = 2*240
        camera_w = 2*320

        layout = {'screen': {'size': (w, h), 'color': (0, 0, 0), 'type': 'normal',
                             'Fps': 60, 'caption': 'this is an example'},
                  'camera':{'class':'MjpegStream','parm':{'size':(camera_w,camera_h),'position':(int(w/2),int(h/2)),
                            'anchor':'center','visible':True,'start':True,'url':'http://192.168.1.1:8080/?action=stream'}},
                  'ssvep1': {'class': 'sinCircle', 'parm': {'radius':65, 'position': (int(0.5*w-320-65), int(0.5*h-240+30)),
                        'text':'forward','textsize':20,'frequency': 6.6, 'visible': True, 'start': False}},
                  'ssvep2': {'class': 'sinCircle', 'parm': {'radius':65, 'position': (int(0.5*w-320-65), int(0.5*h)),
                        'text':'left','textsize':20,'frequency': 7.6, 'visible': True, 'start': False}},
                  'ssvep3': {'class': 'sinCircle', 'parm': {'radius':65, 'position': (int(0.5*w-320-65), int(0.5*h+240-30)),
                        'text':'r-left','textsize':20,'frequency': 8.6, 'visible': True, 'start': False}},
                  'ssvep4': {'class': 'sinCircle', 'parm': {'radius':65, 'position': (int(0.5*w+320+65), int(0.5*h-240+30)),
                        'text':'backward','textsize':20,'frequency': 9.3, 'visible': True, 'start': False}},
                  'ssvep5': {'class': 'sinCircle', 'parm': {'radius':65, 'position': (int(0.5*w+320+65), int(0.5*h)),
                        'text':'right','textsize':20,'frequency': 12.2, 'visible': True, 'start': False}},
                  'ssvep6': {'class': 'sinCircle', 'parm': {'radius':65, 'position': (int(0.5*w+320+65), int(0.5*h+240-30)),
                        'text':'r-right','textsize':20,'frequency': 13.8, 'visible': True, 'start': False}},
                  }

        self.gui = GuiIF(None,layout)
        _ = multiprocessing.Process(target=guiengine_proc,args=(self.gui.args,))
        _.start()
        self.gui.wait()

        sp_ip = self.configs['signal_processing']['sp_host_ip']
        sp_port = self.configs['signal_processing']['sp_host_port']
        self.marker = Marker((sp_ip,sp_port))

        self.TEST_NUM = 12
        self.test_count = 1
        
        self.ROBOT = WIFIROBOT_CTR()

    def transition(self,phase):
        write_log(phase)
        if phase == 'test':
            self.gui.update({'ssvep1': {'start': True,'bordercolor':(0,0,0)}, 'ssvep2': {'start': True,'bordercolor':(0,0,0)}, 'ssvep3': {'start': True,'bordercolor':(0,0,0)},
                             'ssvep4': {'start': True,'bordercolor':(0,0,0)},'ssvep5': {'start': True,'bordercolor':(0,0,0)},'ssvep6': {'start': True,'bordercolor':(0,0,0)}}, {})

            t = global_clock()
            self.marker.send_marker({'process':{'value':[1],'timestamp':[t]}})    #开始测试

        elif phase == 'relax':
            self.gui.update({'ssvep1': {'start': False,'bordercolor':(0,0,0)}, 'ssvep2': {'start': False,'bordercolor':(0,0,0)}, 'ssvep3': {'start': False,'bordercolor':(0,0,0)},
                             'ssvep4': {'start': False,'bordercolor':(0,0,0)},'ssvep5': {'start': False,'bordercolor':(0,0,0)},'ssvep6': {'start': False,'bordercolor':(0,0,0)}}, {})

            self.marker.send_marker({'process': {'value': [2],'timestamp':[global_clock()]}})  #测试完成

            self.test_count += 1
            if self.test_count > self.TEST_NUM:
                self.change_phase('rrelax')

    def stop_run(self):
        self.marker.send_marker({'endsigpro': {'value':[1],'timestamp':[global_clock()]}})  #测试完成
        self.gui.quit()
        self.ROBOT.close()

    def process(self,result):
        if result is not None:
            print(result)
            self.gui.update({'ssvep%s'%(result+1): {'bordercolor':(255,0,0)}},{})
            self.ROBOT.go(cmdss[result][0],cmdss[result][1])
            

if __name__ == '__main__':
    app = bciApp()
    app.start_run()


