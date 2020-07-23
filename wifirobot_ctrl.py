#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/10/12 11:48
# @Version : 1.0
# @File    : wifirobot_ctrl.py
# @Author  : Jingsheng Tang
# @Version : 1.0
# @Contact : mrtang@nudt.edu.cn   mrtang_cs@163.com
# @License : (C) All Rights Reserved


import socket
import threading
import time

CMDS = {'forward':  b'\xff\x00\x01\x00\xff',
       'backward':  b'\xff\x00\x02\x00\xff',
       'left':      b'\xff\x00\x03\x00\xff',
       'right':     b'\xff\x00\x04\x00\xff',
       'fleft':     b'\xff\x00\x05\x00\xff',
       'fright':    b'\xff\x00\x06\x00\xff',
       'bleft':     b'\xff\x00\x07\x00\xff',
       'bright':    b'\xff\x00\x08\x00\xff',
       'rleft':     b'\xff\x00\x09\x00\xff',
       'rright':    b'\xff\x00\x10\x00\xff',
       'stop':      b'\xff\x00\x00\x00\xff',
       }
       
__INF__ = float('inf')

class WIFIROBOT_CTR():
    '''
    supportted command:
            'forward',  'backward', 'left',     'right',    'fleft',
            'fright',   'bleft',    'bright',   'rleft',    'rright',
           'stop'
    useage:
        wr = WIFIROBOT_CTR()
        wr.go(cmd)
    '''
    def __init__(self,ip='192.168.1.1',port=2001):
        self._lock = threading.Lock()
        self.ip = ip
        self.port = port
        self._close = False
        self.CMDBUF = CMDS['stop']
        self.stp = 0.2
        self.cmd_count = 0

        cmdthread = threading.Thread(target=self.run, args=(),daemon=True)
        cmdthread.start()

    def run(self):
        self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.s.connect((self.ip,self.port))
        while not self._close:
            if self.cmd_count > 0:
                self.cmd_count -= 1
            else:
                self.CMDBUF = CMDS['stop']

            self.s.send(self.CMDBUF)
            time.sleep(self.stp)

    def go(self,cmd,*arg):
        if cmd in CMDS:
            if len(arg)>0:
                self.cmd_count = int(arg[0]/self.stp)
            else:
                self.cmd_count = __INF__
            self._lock.acquire()
            self.CMDBUF = CMDS[cmd]
            self._lock.release()
        else:
            print('[wifi robot ctr] error command: ',cmd)

    def close(self):
        self.go('stop')
        time.sleep(0.3)
        self._close = True
        time.sleep(0.3)


if __name__ == '__main__':
    wr = WIFIROBOT_CTR()
    # for cmd in CMDS:
        # print(cmd)
        # wr.go1(cmd,1)
        # time.sleep(3)
    wr.go1('right',1)
    




