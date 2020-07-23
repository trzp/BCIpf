#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/11/11 10:40
# @Version : 1.0
# @File    : k.py
# @Author  : Jingsheng Tang
# @Version : 1.0
# @Contact : mrtang@nudt.edu.cn   mrtang_cs@163.com
# @License : (C) All Rights Reserved


import csv

dic = {'a':1,'b':2,'c':3,'d':4}
head = ['a','b','c','d']

f = open('f:\\data\\tjs.csv','w',newline='')
fcsv = csv.DictWriter(f,head)
fcsv.writeheader()
fcsv.writerow(dic)
f.flush()

