#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17/6/14 18:04
# https://github.com/Shinlor/WinRoute/blob/master/winroute/winroute.py
import ctypes
import socket
import struct


def getroute():
    DWORD = ctypes.c_ulong
    NULL = ""
    NO_ERROR = 0
    bOrder = 0
    ANY_SIZE = 1

    class MIB_IPFORWARDROW(ctypes.Structure):

        _fields_ = [('dwForwardDest', DWORD),  # 目标IP
                    ('dwForwardMask', DWORD),  # 网络掩码
                    ('dwForwardPolicy', DWORD),  # 多径路由策略
                    ('dwForwardNextHop', DWORD),  # 下一跳IP
                    ('dwForwardIfIndex', DWORD),  # 接口索引
                    ('dwForwardType', DWORD),  # 路由类型
                    ('dwForwardProto', DWORD),  # 路由协议
                    ('dwForwardAge', DWORD),  # 路由时间
                    ('dwForwardNextHopAS', DWORD),  # 下一跳编号
                    ('dwForwardMetric1', DWORD),  # 跃点数
                    ('dwForwardMetric2', DWORD),
                    ('dwForwardMetric3', DWORD),
                    ('dwForwardMetric4', DWORD),
                    ('dwForwardMetric5', DWORD)]

    dwSize = DWORD(0)
    IpForwardTablelist = []

    # call once to get dwSize
    dwStatus = ctypes.windll.iphlpapi.GetIpForwardTable(NULL, ctypes.byref(dwSize), bOrder)
    # print (dwStatus)

    # ANY_SIZE is used out of convention (to be like MS docs); even setting this
    # to dwSize will likely be much larger than actually necessary but much
    # more efficient that just declaring ANY_SIZE = 65500.
    # (in C we would use malloc to allocate memory for the *table pointer and
    #  then have ANY_SIZE set to 1 in the structure definition)

    ANY_SIZE = dwSize.value

    class MIB_IPFORWARDTABLE(ctypes.Structure):

        _fields_ = [('dwNumEntries', DWORD),
                    ('table', MIB_IPFORWARDROW * ANY_SIZE)]

    # print (ANY_SIZE)

    IpForwardTable = MIB_IPFORWARDTABLE()

    if (ctypes.windll.iphlpapi.GetIpForwardTable(ctypes.byref(IpForwardTable),
                                                 ctypes.byref(dwSize), bOrder) == NO_ERROR):

        maxNum = IpForwardTable.dwNumEntries
        # print(IpForwardTable.dwNumEntries)
        # print(IpForwardTable.table)
        placeHolder = 0

        # loop through every connection
        while placeHolder < maxNum:
            item = IpForwardTable.table[placeHolder]
            IpForwardDcit = {}
            placeHolder += 1
            ForwardNextHop = item.dwForwardNextHop

            ForwardDest = item.dwForwardDest
            ForwardDest = socket.inet_ntoa(struct.pack('L', ForwardDest))

            ForwardMask = item.dwForwardMask
            ForwardMask = socket.inet_ntoa(struct.pack('L', ForwardMask))

            ForwardPolicy = item.dwForwardPolicy
            ForwardPolicy = socket.inet_ntoa(struct.pack('L', ForwardPolicy))

            ForwardNextHop = item.dwForwardNextHop
            # 使用socket模块，转换32位打包的IPV4地址为IP地址的标准点号分隔字符串表示
            ForwardNextHop = socket.inet_ntoa(struct.pack('L', ForwardNextHop))
            ForwardIfIndex = item.dwForwardIfIndex
            ForwardType = item.dwForwardType
            ForwardProto = item.dwForwardProto

            ForwardAge = item.dwForwardAge

            ForwardNextHopAS = item.dwForwardNextHopAS

            ForwardMetric1 = item.dwForwardMetric1
            ForwardMetric2 = item.dwForwardMetric2
            ForwardMetric3 = item.dwForwardMetric3
            ForwardMetric4 = item.dwForwardMetric4
            ForwardMetric5 = item.dwForwardMetric5

            # 字典IpForwardDcit赋值
            IpForwardDcit["ForwardDest"] = ForwardDest
            IpForwardDcit["ForwardMask"] = ForwardMask
            IpForwardDcit["ForwardPolicy"] = ForwardPolicy
            IpForwardDcit["ForwardNextHop"] = ForwardNextHop
            IpForwardDcit["ForwardIfIndex"] = ForwardIfIndex
            IpForwardDcit["ForwardType"] = ForwardType
            IpForwardDcit["ForwardProto"] = ForwardProto
            IpForwardDcit["ForwardAge"] = ForwardAge
            IpForwardDcit["ForwardNextHopAS"] = ForwardNextHopAS
            IpForwardDcit["ForwardMetric1"] = ForwardMetric1
            IpForwardDcit["ForwardMetric2"] = ForwardMetric2
            IpForwardDcit["ForwardMetric3"] = ForwardMetric3
            IpForwardDcit["ForwardMetric4"] = ForwardMetric4
            IpForwardDcit["ForwardMetric5"] = ForwardMetric5

            IpForwardTablelist.append(IpForwardDcit)

    return IpForwardTablelist
