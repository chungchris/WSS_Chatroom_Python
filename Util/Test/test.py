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
parser.add_argument('-u', '--users', dest='users', default=3, type=int, \
                    help=f'simulate how many users')
parser.add_argument('-f', '--frequency', dest='frequency', default=5, type=int, \
                    help=f'e.g. 5: simulate each user to send msg by frequency every t seconds. t will be a random value from 1 to 5.')
parser.add_argument('-a', '--amount-of-msg', dest='amount', default=20, type=int, \
                    help=f'amount of messages each user will send')
args, unknown = parser.parse_known_args()

# start a server process
'''
import subprocess
try:
    subprocess.run(['python3.7','wss_server.py','-u','5566','-p',f'{args.port}','-d','0'])
except Exception as e:
    print(f'run server error:{e}')
    sys.exit(0)
'''
import os
from multiprocessing import Process

try:
    def runServer():
        os.system(f"python3.7 ../../Server/wss_server.py -u 5566 -p {args.port}")
    p = Process(target=runServer)
    p.start()
except Exception as e:
    print(f'### tester ### run server error:{e}')
    sys.exit(0)
print(f'### tester ### server started')

# start wss client gui for each user in indep process
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

def genTest(file_name):
    with open(file_name, 'w') as f:
        for _ in range(10):
            n = '\n'
            f.write(f'sleep2{n}')
    '''
    wsg.cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_REG, name, '5566'))
    wsg.cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_LOGIN, name, '5566'))
    for _ in range(a):
        t = (int(random.random()*(10**power)) % f[1]) + f[0]
        msg = name*t
        if len(msg) > settings.MAX_MSG_LEN:
            msg = msg[:settings.MAX_MSG_LEN]
        wsg.cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_MSG, msg))
    '''
    

import time
def runTest(file_name):
    print(f'to start a client with tc name:{file_name}')
    gui.wssClientGUI(args.port, test=True, test_case=file_name)
    
    '''
    # register
    time.sleep(3)
    wsg.cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_REG, name, '5566'))
    # login
    time.sleep(1)
    wsg.cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_LOGIN, name, '5566'))
    # send msg
    time.sleep(1)
    for _ in range(a):
        t = (int(random.random()*(10**power)) % f[1]) + f[0]
        msg = name*t
        if len(msg) > settings.MAX_MSG_LEN:
            msg = msg[:settings.MAX_MSG_LEN]
        wsg.cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_MSG, msg))
        time.sleep(t)
    # unregister
    time.sleep(2)
    wsg.cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_UNREG))
    '''

names = []
p_clients = []
for i in range(args.users):
    name = genName()
    names.append(name)
    genTest('tc_' + name + '.txt')
for name in names:
    p = Process(target=runTest, args=('tc_' + name + '.txt',))
    p_clients.append(p)
    p.start()
for p in p_clients:
    p.join()

