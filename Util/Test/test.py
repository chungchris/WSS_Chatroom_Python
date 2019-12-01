#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 30 12:20:04 2019

@author: chungchris
"""

import argparse
import math
import os
import random
import sys

from multiprocessing import Process

sys.path.append("../../Client")

import gui
import settings

#####

parser = argparse.ArgumentParser(description='Start WSS Chatroom test.')
parser.add_argument('-m', '--mode', dest='mode', default='test', type=string,\
                    help=f'test, verify, clean')
parser.add_argument('-p', '--port', dest='port', default=settings.DEFAULT_WSS_PORT, \
                    help=f'server at localhost port. default set at {settings.DEFAULT_WSS_PORT}')
parser.add_argument('-u', '--users', dest='users', default=3, type=int, \
                    help=f'simulate how many users')
parser.add_argument('-f', '--frequency', dest='frequency', default=5, type=int, \
                    help=f'e.g. 5: simulate each user to send msg by frequency every t seconds. t will be a random value from 1 to 5.')
parser.add_argument('-a', '--amount-of-msg', dest='amount', default=50, type=int, \
                    help=f'amount of messages each user will send')
args, unknown = parser.parse_known_args()

#####

if args.mode == 'clean':
    os.system(f'rm -rf ./Testcase')
    os.system(f'rm -rf ./server.log')
    os.system(f'rm -rf ./user_book*')
    sys.exit(0)
elif args.mode == 'verify':
    sys.exit(0)
elif args.mode != 'test':
    print('no such mode')
    sys.exit(0)

#####

# start a server process
def runServer():
    os.system(f'python3.7 ../../Server/wss_server.py -u 5566 -p {args.port}')
try:
    p = Process(target=runServer)
    p.start()
except Exception as e:
    print(f'### tester ### run server error:{e}')
    sys.exit(0)
print(f'### tester ### server started')

#####

if args.frequency > 1:
    r = (1, args.frequency)
else:
    r = (1, 5)
power = int(math.log(r[1], 10))+2

names = []
nn = len(settings.ALLOWED_CHAR_FOR_NAME)
ALLOWED_CHAR_FOR_NAME = list(settings.ALLOWED_CHAR_FOR_NAME)

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
            names.append(name)
            break
    return name

def genTest(name):
    file_name = 'tc_' + name + '.txt'
    with open('./Testcase/'+file_name, 'w') as f:
        n = '\n'
        # register
        f.write(f'{settings.JSON_VALUE_REQUEST_TYPE_REG};{name};5566{n}')
        f.write(f'sleep2{n}')
        # login
        f.write(f'{settings.JSON_VALUE_REQUEST_TYPE_LOGIN};{name};5566{n}')
        f.write(f'sleep2{n}')
        # send msgs
        for _ in range(args.amount):
            t = (int(random.random()*(10**power)) % r[1]) + r[0]
            msg = name*t
            if len(msg) > settings.MAX_MSG_LEN:
                msg = msg[:settings.MAX_MSG_LEN]
            f.write(f'{settings.JSON_VALUE_REQUEST_TYPE_MSG};{msg}{n}')
            f.write(f'sleep{t}{n}')
        # unregister
        f.write(f'{settings.JSON_VALUE_REQUEST_TYPE_UNREG};{name}{n}')
        f.write(f'sleep2{n}')

def runTest(file_name):
    print(f'### tester ### to start a client with tc name:{file_name}')
    gui.wssClientGUI(args.port, test=True, test_case=file_name)

try:
    os.mkdir('Testcase')
except FileExistsError:
    pass
for i in range(args.users):
    name = genName()
    genTest(name)
print('### tester ### test cases generated under ./Testcase/')

# start wss client gui for each user in indep process
p_clients = []
for name in names:
    p = Process(target=runTest, args=('tc_' + name + '.txt',))
    p_clients.append(p)
    p.start()
for p in p_clients:
    p.join()

