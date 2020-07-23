#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/8/27 14:49
# @Version : 1.0
# @File    : storagev1_2.py
# @Author  : Jingsheng Tang
# @Version : 1.0
# @Contact : mrtang@nudt.edu.cn   mrtang_cs@163.com
# @License : (C) All Rights Reserved

import os
import time
from multiprocessing import Queue,Event
import multiprocessing
import numpy as np
import csv

class Store():
    def __init__(self,configs):
        self.configs = configs
        self.OK = False

    def prefile(self):
        # 生成文件名
        head = self.configs['subject'] + '-S%02iR' % (self.configs['session'])  #eg. sub-EEG-S01R
        filename = head + '001'
        newfilename = self.configs['storage path'] + '//' + filename
        if not os.path.exists(self.configs['storage path']): # 没有目录则创建目录
            os.makedirs(self.configs['storage path'])
        else:
            files = os.listdir(self.configs['storage path']) # 遍历所有文件
            nums = [self.getnum(f, head) for f in files if self.getnum(f, head) > -1]
            if nums != []:    newfilename = self.configs['storage path'] + '//' + head + '%03i' % (max(nums) + 1)

        self.marker_file_name = newfilename + "_mkr.csv"
        self.eeg_file_name = newfilename + "_eeg.csv"

        self.eeg_header_key = ["subject","filename","time","eeg channels","eeg channel label",
                   "ref channels","ref channel label","samplingrate","amplifier"]
        self.mkr_header_key = ["subject","filename", "time","samplingrate", "amplifier"]
        timestr = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
        self.eeg_header_value = [self.configs['subject'],self.eeg_file_name,timestr,self.configs['eeg channels'],self.configs['eeg channel label'],
                                 self.configs['ref channels'],self.configs['ref channel label'],self.configs['samplingrate'],self.configs['amplifier']]
        self.mkr_header_value = [self.configs['subject'],self.marker_file_name,timestr,self.configs['samplingrate'],self.configs['amplifier']]

        self.eegfile = open(self.eeg_file_name,'w',newline='')
        self.eegcsv = csv.writer(self.eegfile)
        self.eegcsv.writerow(self.eeg_header_key)
        self.eegcsv.writerow(self.eeg_header_value)
        self.eegcsv.writerow(self.configs['eeg channels'])
        self.eegcsv.writerow([])
        self.eegfile.flush()


        self.mkrfile = open(self.marker_file_name, 'w', newline='')
        self.mkrcsv = csv.writer(self.mkrfile)

        self._markers_ = {}
        self._eeg_ = []
        self.eegCLK = time.clock()
        self.mkrCLK = time.clock()
        self.OK = True

        print('[storage module] ready:\n>>>> eegfile: %s \n>>>> mkrfile: %s' % (self.eeg_file_name, self.marker_file_name))

    def getnum(self,file,head):
        hi = file.find(head)
        if hi==-1:  # 没有搜索到特征命名
            return -1
        else:       # 搜索到特征命名
            try:
                filename,_ = os.path.splitext(file)
                num = int(filename[hi+len(head):-4])
                return num
            except:
                return -1

    def write_eeg(self,eegs):   #逐行写入
        if not self.OK: return
        self._eeg_.append(eegs)
        nCLK = time.clock()
        if nCLK - self.eegCLK > 5:
            self.eegCLK = nCLK
            tem = np.vstack(self._eeg_)
            self._eeg_ = []
            self.eegcsv.writerows(tem)
            self.eegfile.flush()

    def write_mkr(self,marker):
        # marker: eg. {'mkr1':{'value':[0],'timepoint':[100]},'mkr2':{'value':[1,2],'timepoint':[200,250]}}
        # 更新marker

        if not self.OK:  return
        for key in marker:
            mkr = marker[key]
            mk = np.array([mkr['value'], mkr['timepoint']])
            if key in self._markers_:
                self._markers_[key] = np.hstack([self._markers_[key], mk])
            else:
                self._markers_[key] = mk

        nCLK = time.clock()
        if nCLK - self.mkrCLK > 5:
            self.mkrfile.truncate(0) #清空重写
            self.mkrCLK = nCLK
            self.mkrcsv.writerow(self.mkr_header_key)
            self.mkrcsv.writerow(self.mkr_header_value)
            self.mkrcsv.writerow([])
            for key in self._markers_:
                self.mkrcsv.writerow([key])
                self.mkrcsv.writerows(self._markers_[key])
            self.mkrfile.flush()

    def close(self):
        self.mkrfile.close()
        self.eegfile.close()

# 一般情况为storage模块开启一个独立进程
class StorageInterface():
    def __init__(self):
        self.ok = Event()
        self.ev = Event()
        self.que = Queue()
        self.args = {'ev':self.ev,'que':self.que,'ok':self.ok}

    def write_eeg_to_file(self,eeg):
        '''
        eeg:  ch x N
        '''
        if eeg is not None:
            self.que.put(['eeg',eeg[0].transpose()])
            
    def new_record(self):
        self.que.put(['new-record',''])
    
    def end_record(self):
        self.que.put(['end-record',''])

    def write_mkr_to_file(self,mkr):
        if len(mkr)>0:
            self.que.put(['mkr',mkr])

    def close(self):
        self.que.put(['end',''])
        self.ev.set()

    def wait(self):
        self.ok.wait()

    def __del__(self):
        self.que.put(['end', ''])
        self.ev.set()

def storage_pro(args,configs):
    ok = args['ok']
    ev = args['ev']
    que = args['que']
    st = Store(configs)
    ok.set() #发送初始化完成的状态

    while not ev.is_set():
        flg,buf = que.get()
        if flg == 'eeg':
            st.write_eeg(buf)
        elif flg == 'mkr':
            st.write_mkr(buf)
        elif flg == 'new-record':       #创建一个新文件
            st.prefile()
        elif flg == 'end-record':
            st.close()
            st.OK = False               # 停止当前记录
        else:
            pass
    print('[storage module] process exit')

def main():
    with open(r'./config.js', 'r') as f:
        config = json.load(f)
    config = config['signal_processing']

    eegamp = EEGamp(100, config['eeg channels'])
    stIF = StorageInterface()
    p = multiprocessing.Process(target=storage_pro, args=(stIF.args, config))
    p.start()
    stIF.wait()

    stIF.new_record()
    # for i in range(100):
    #     data = eegamp.read()
    #     stIF.write_eeg_to_file(data)
    #     time.sleep(0.1)

    for i in range(100):
        stIF.write_mkr_to_file({'marker1':{'value':[random.randint(0,10)],'timepoint':[time.clock()]}})
        time.sleep(0.1)

    for i in range(100):
        stIF.write_mkr_to_file({'marker2':{'value':[random.randint(0,10)],'timepoint':[time.clock()]}})
        time.sleep(0.1)

    stIF.end_record()

    stIF.close()

if __name__ == '__main__':
    import json
    import random
    from signal_generator import EEGamp
    main()





