#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/9/16 20:41
# @Version : 1.0
# @File    : coder.py
# @Author  : Jingsheng Tang
# @Version : 1.0
# @Contact : mrtang@nudt.edu.cn   mrtang_cs@163.com
# @License : (C) All Rights Reserved

import json

class DefaultCoder():
    def __init__(self):
        pass

    def encode(self,obj):
        return json.dumps(obj)

    def decode(self,buf):
        return json.loads(buf)


