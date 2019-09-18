#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Copyright (C) 2018, Nudt, JingshengTang, All Rights Reserved
#Author: Jingsheng Tang
#Email: mrtang@nudt.edu.cn

from __future__ import print_function
import time
import multiprocessing
from multiprocessing import Queue
# from rz_global_clock import global_clock as sysclock  # 不要随意载入
from rz_clock import clock as sysclock

self_name = 'Phase'

try:    __INF__ = float('inf')
except: __INF__ = 0xFFFF

def register_phase(arg):        
    PHASES = {}
    PHASES['start'] = {'next': '', 'duration': __INF__}
    PHASES['stop'] = {'next': '', 'duration': __INF__}
    for item in arg:
        if 'duration' in item:
            PHASES[item['name']]={'next':item['next'],'duration':item['duration']}
        else:
            PHASES[item['name']]={'next':'','duration':__INF__}
    return PHASES

def write_log(m):
    print('[%s][%3.4f]%s'%(self_name,sysclock(),m))

def phase_process(phase_list,Q_p2c,Q_c2p):
    #phase_list:
    #接受一个列表，每一个元素是一个字典，用来描述这个phase
    #e.g.
    # ph = [  {'name':'start','next':'prompt','duration':1},
             # {'name':'prompt','next':'on','duration':1},
         # ]
    #Q_p2c: multiprocessing.Queue  phase -> core
    #Q_c2p: multiprocessing.Queue  core -> phase

    PHASES = register_phase(phase_list)
    time.sleep(1.5)
    current_phase = 'start' #phase必须从start开始
    Q_p2c.put(current_phase)
    _clk = sysclock()

    while True:
        clk = sysclock()

        # 按时间节奏跳转
        cdur = PHASES[current_phase]['duration']
        if clk - _clk >= cdur:
            current_phase = PHASES[current_phase]['next']
            Q_p2c.put(current_phase)
            _clk = _clk + cdur  #避免累计误差

        # 自定义跳转
        if not Q_c2p.empty():
            typ,p = Q_c2p.get()
            if typ == 'change':
                if p in PHASES:
                    current_phase = p
                    Q_p2c.put(current_phase)
                    _clk = clk
                else:
                    print('[phase][warning]change phase ?? <%s %s>'%(typ,p))
            else:
                pass

        if current_phase == 'stop': break
        time.sleep(0.005)

    print('[phase][info] process ended')

class phaseInterface():
    def __init__(self,phase = []):
        self.phase_list = phase
        self.Q_p2c = Queue()
        self.Q_c2p = Queue()
        self.args = (phase,self.Q_p2c,self.Q_c2p)
        self._phases_ = register_phase(phase)
    
    def change_phase(self,phase):
        self.Q_c2p.put(['change',phase])
    
    def next_phase(self):
        return self.Q_p2c.get()
        
if __name__ == '__main__':
    phase = [ {'name':'start','next':'prompt','duration':1},
              {'name':'prompt','next':'que'},
              {'name':'que','next':'stop','duration':4}
            ]
            
    ph = phaseInterface(phase)
    ph_proc = multiprocessing.Process(target = phase_process,args = ph.args)
    ph_proc.start()
    
    while True:
        current_phase = ph.next_phase()
        
        if current_phase == 'stop': break
        if current_phase == 'prompt':
            time.sleep(3)
            ph.change_phase('que')
        if current_phase == 'stop': break
