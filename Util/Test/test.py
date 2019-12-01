#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 30 12:20:04 2019

@author: chungchris
"""

import sys
sys.path.append("../../Client")
import gui
import settings


import argparse
parser = argparse.ArgumentParser(description='Start WSS Chatroom test.')
parser.add_argument('-p', '--port', dest='port', default=settings.DEFAULT_WSS_PORT, \
                    help=f'server at localhost port. default set at {settings.DEFAULT_WSS_PORT}')
parser.add_argument('-f', '--frequency', dest='frequency', default=5, type=int, \
                    help=f'e.g. 5: simulate each user to send msg by frequency every t seconds. t will be a random value from 1 to 5.')
parser.add_argument('-a', '--amount-of-msg', dest='amount', default=20, type=int, \
                    help=f'amount of messages each user will send')
args, unknown = parser.parse_known_args()

# start a server process
import subprocess
try:
    subprocess.run(['python3.7','wss_server.py','-u','5566','-p',f'{args.port}','-d','0'])
except Exception as e:
    print('run server error:{e})
    sys.exit(0)
import os
from multiprocessing import Process

#def runServer():
#    os.system(f"python wss_server.py -u 5566 -p {args.port}")
#p = Process(target=runServer)
#p.start()
#p.join()

# start wss client gui for each user in indep process
cn = 2

if args.frequency > 1:
    f = (1, args.frequency)
else:
    f = (1, 5)
import math
power = int(math.log(f[1], 10))+2

a = args.amount
nn = len(settings.ALLOWED_CHAR_FOR_NAME)
ALLOWED_CHAR_FOR_NAME = list(settings.ALLOWED_CHAR_FOR_NAME)

import random
names = set()
def genName():
    while True:
        name = ''
        t = int(random.random()*100) % nn
        name += ALLOWED_CHAR_FOR_NAME[t]
        t = int(random.random()*100) % nn
        name += ALLOWED_CHAR_FOR_NAME[t]
        t = int(random.random()*100) % nn
        name += ALLOWED_CHAR_FOR_NAME[t]
        if name not in names:
            names.add(name)
            break
    return name

import time
def runTest(name):
    wsg = gui.wssClientGUI()
    # register
    time.sleep(3)
    wsg.cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_REG, name, '5566'))
    # login
    time.sleep(1)
    wsg.cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_LOGIN, name, '5566'))
    # send msg
    time.sleep(1)
    for _ in range(a):
        t = (int(random.random()*(10**power)) % f) + f[0]
        msg = name*t
        if len(msg) > settings.MAX_MSG_LEN:
            msg = msg[:settings.MAX_MSG_LEN]
        wsg.cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_MSG, msg))
        time.sleep(t)
    # unregister
    time.sleep(2)
    wsg.cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_UNREG))


for i in range(cn):
    p = Process(target=runTest, args=(genName(), ))
    p.start()
    p.join()

