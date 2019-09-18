#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/8/26 19:11
# @Version : 1.0
# @File    : sync_sock.py
# @Author  : Jingsheng Tang
# @Version : 1.0
# @Contact : mrtang@nudt.edu.cn   mrtang_cs@163.com
# @License : (C) All Rights Reserved

from sync_sock import *

s = SyncClient(('127.0.0.1',9000))
s.start_sync()
