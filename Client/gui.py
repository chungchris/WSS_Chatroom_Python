#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 14:22:34 2019

@author: chungchris
"""

import argparse
import logging
import sys
import time
import threading
import tkinter as tk
import queue

import settings
import wss_client

#####

guiReady = False

client = None
obj_chat_room = None
status_label_text = None
status_label_color = None

last_send_time = None

#####

def wssClientGUIMain(cmd_q):
    global status_label_text, status_label_color
    
    window = tk.Tk()
    window.title('WSSChatroomClient')
    window.geometry('800x600')
    window.configure(background='white')
    
    header_label = tk.Label(window, text='Chatroom')
    header_label.pack()

    top_frame = tk.Frame(window)
    text_frame = tk.Frame(window, height=10)
    status_frame = tk.Frame(window)
    login_frame = tk.Frame(window)
    
    def isUsableName(name):
        if len(name) > settings.ALLOWED_LEN_FOR_NAME:
            return False
        for c in name:
            if c not in settings.ALLOWED_CHAR_FOR_NAME:
                return False
        return True
    def isUsablePW(pw):
        if len(pw) > settings.ALLOWED_LEN_FOR_PASSWORD_MAX \
            or len(pw) < settings.ALLOWED_LEN_FOR_PASSWORD_MIN:
            return False
        for c in pw:
            if c not in settings.ALLOWED_CHAR_FOR_PASSWORD:
                return False
        return True
    
    def register():
        if client.status != settings.USER_STATE_INITIAL:
            status_label_text.set(settings.UI_STATUS_MSG_INITIAL)
            status_label_color('red')
            return
        name = name_entry.get()
        pw = pw_entry.get()
        if len(name)<1 or not isUsableName(name):
            status_label_text.set(settings.UI_STATUS_MSG_INVALID_REG_NAME)
            status_label_color('red')
            return
        if len(pw)<1 or not isUsablePW(pw):
            status_label_text.set(settings.UI_STATUS_MSG_INVALID_REG_PW)
            status_label_color('red')
            return
        cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_REG, name, pw))
    def unregister():
        if client.status != settings.USER_STATE_LOGIN:
            return
        cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_UNREG, client.name))
    def login():
        if client.status != settings.USER_STATE_INITIAL:
            status_label_text.set(settings.UI_STATUS_MSG_INITIAL)
            status_label_color('red')
            return
        name = name_entry.get()
        pw = pw_entry.get()
        if len(name)<1 or not isUsableName(name):
            status_label_text.set(settings.UI_STATUS_MSG_INVALID_REG_NAME)
            status_label_color('red')
            return
        if len(pw)<1 or not isUsablePW(pw):
            status_label_text.set(settings.UI_STATUS_MSG_INVALID_REG_PW)
            status_label_color('red')
            return
        cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_LOGIN, name, pw))
    def send(event=None):
        logger.debug('send event handler')
        if client.status != settings.USER_STATE_LOGIN:
            text_text.delete('1.0', tk.END)
            status_label_text.set(settings.UI_STATUS_MSG_INITIAL)
            status_label_color('red')
            return
        
        # avoid too frequent sending
        global last_send_time
        now = time.time()
        if last_send_time != None:
            if (now - last_send_time) < settings.MIN_SEND_MSG_INTERVAL:
                logger.debug('sending too frequent')
                return
        last_send_time = now
        
        text = text_text.get('1.0', tk.END)
        l = len(text)
        text = text.strip('\n')
        text = text.strip()
        if l>0:
            if l > settings.MAX_MSG_LEN:
                text = text[:settings.MAX_MSG_LEN]
            cmd_q.put((settings.JSON_VALUE_REQUEST_TYPE_MSG, text))
            text_text.delete('1.0', tk.END)
    
    # top_frame: chat room
    vbar = tk.Scrollbar(top_frame, orient=tk.VERTICAL)
    vbar.pack(side=tk.RIGHT, fill=tk.Y)
    hbar = tk.Scrollbar(top_frame, orient=tk.HORIZONTAL)
    hbar.pack(side=tk.BOTTOM, fill=tk.X)
    room = tk.Listbox(top_frame, bg='white', relief=tk.SUNKEN, bd=5)
    vbar.config(command=room.yview)
    room.config(yscrollcommand=vbar.set)
    hbar.config(command=room.xview)
    room.config(xscrollcommand=hbar.set)
    room.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
    top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    
    # text frame: test msg to send
    text_vbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL)
    text_text = tk.Text(text_frame, bg='grey', cursor='arrow', height=3, fg='white')
    text_vbar.config(command=text_text.yview)
    text_text.config(yscrollcommand=text_vbar.set)
    text_text.pack(side=tk.LEFT, fill=tk.Y, expand=False)
    text_vbar.pack(side=tk.LEFT)
    text_text.insert(tk.END, 'text here...')
    send_button = tk.Button(text_frame, text='SEND', fg='black', command=send)
    send_button.pack(side=tk.LEFT)
    
    # status frame
    status_label_text = tk.StringVar()
    status_label_text.set('...status...')
    def set_tatus_label_color(color):
        status_label.config(fg=color)
    status_label_color = set_tatus_label_color
    status_label = tk.Label(status_frame, textvariable=status_label_text, fg='black')
    status_label.pack(side=tk.TOP)
    
    # login frame: register/login/status
    name_label = tk.Label(login_frame, text='Name')
    name_label.pack(side=tk.LEFT)
    name_entry = tk.Entry(login_frame)
    name_entry.pack(side=tk.LEFT)
    pw_label = tk.Label(login_frame, text='Password')
    pw_label.pack(side=tk.LEFT)
    pw_entry = tk.Entry(login_frame)
    pw_entry.pack(side=tk.LEFT)
    reg_button = tk.Button(login_frame, text='Register', fg='black', command=register)
    reg_button.pack(side=tk.LEFT)
    login_button = tk.Button(login_frame, text='Login', fg='black', command=login)
    login_button.pack(side=tk.LEFT)
    unreg_button = tk.Button(login_frame, text='Unregister', fg='black', command=unregister)
    unreg_button.pack(side=tk.LEFT)
    
    #text_frame.bind('<Return>', send)
    #login_frame.bind('<Return>', send)
    #status_frame.bind('<Return>', send)
    window.bind('<Return>', send)
    
    login_frame.pack(side=tk.BOTTOM)
    status_frame.pack(side=tk.BOTTOM)
    text_frame.pack(side=tk.BOTTOM, fill=None, expand=False)
    
    global obj_chat_room
    obj_chat_room = room
    
    global guiReady
    guiReady = True
    logger.warning('GUI ready')
    window.mainloop()
    
# running on wss_client_thread
def startWSSClient():
    logger.warning('start wss client agent thread')
    while not guiReady:
        time.sleep(0.1)
    
    # call wss_client
    # this thread will be blocked by async loop
    global cmd_q, client, obj_chat_room, status_label_text, status_label_color
    client = wss_client.Client(args.port)
    client.startFromGUI(cmd_q, \
                        obj_chat_room, status_label_text, status_label_color)

#####

# set logger
logger = logging.getLogger()
logging.basicConfig(filename=settings.LOG_FILE)

parser = argparse.ArgumentParser(description='Start a WSS Client GUI.')
parser.add_argument('-p', '--port', dest='port', default=settings.DEFAULT_WSS_PORT, \
                    help=f'connecting to server at localhost port. default set at {settings.DEFAULT_WSS_PORT}')
parser.add_argument('-d', '--debug', dest='debug', type=int, \
                    help=f'number. enable debug log or not. (default) 0- disabled; 1- enabled. log file is {settings.LOG_FILE}; 2- enabled and print to stderr as well')
args, unknown = parser.parse_known_args()

if args.debug:
    if args.debug == 0:
        debug = False
    elif args.debug == 1 or args.debug == 2:
        debug = True
    else:
        debug = False
else:
    debug = False

if settings.DEBUG and debug:
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s%(funcName)s:%(lineno)i - %(message)s')
else:
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

from logging.handlers import RotatingFileHandler
# TODO: test whether rotate actually work
log_file_handler = RotatingFileHandler(settings.LOG_FILE, mode='a', \
                                       maxBytes=settings.MAX_LOG_SIZE*1024*1024, \
                                       backupCount=2, encoding=None, delay=0)
log_file_handler.setFormatter(log_formatter)

if settings.DEBUG:
    logger.setLevel(logging.DEBUG)
    log_file_handler.setLevel(logging.DEBUG)
    if args.debug and args.debug == 2:
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.DEBUG)
        stderr_handler.setFormatter(log_formatter)
        logger.addHandler(stderr_handler)
else:
    logger.setLevel(logging.WARNING)
    my_handler.setLevel(logging.WARNING)
logger.addHandler(log_file_handler)
    
# start wss client agent
wss_client_thread = threading.Thread(target=startWSSClient, name='wss_client_thread')
wss_client_thread.daemon = True  # as soon as the main program exits, all the daemon threads are killed
wss_client_thread.start()
    
# create q for gui event handler to pass action to wss_client
cmd_q = queue.Queue()

# start gui running on main thread
wssClientGUIMain(cmd_q)
logger.warning('window closed')
    