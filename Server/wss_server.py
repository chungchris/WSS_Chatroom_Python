#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 22 20:42:45 2019

@author: chungchris
"""

import argparse
import asyncio
import json
import logging
import os
import pathlib
import ssl
import sys
#import traceback

import websockets

from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto import Random

import settings

##########

needIncludePath = []

##########

class User:
    def __init__(self, name, pw):
        self.name = name  # unique in user book
        self.password = pw  # TODO: hash first

class UserBook:
    def __init__(self, pw):
        self.users = []
        self.updated = True
        self.password = pw
        self.chunksize = 64*1024
        self._load()
    
    def _getKey(self, password):
        hasher = SHA256.new(password.encode('utf-8'))
        return hasher.digest()
    def _encrypt(self, key, filename):
        outputFile = filename + '.aes'
        filesize = str(os.path.getsize(filename)).zfill(16)
        IV = Random.new().read(16)
        encryptor = AES.new(key, AES.MODE_CBC, IV)
        with open(filename, 'rb') as infile:
            with open(outputFile, 'wb') as outfile:
                outfile.write(filesize.encode('utf-8'))
                outfile.write(IV)
                while True:
                    chunk = infile.read(self.chunksize)
                    if len(chunk) == 0:
                        break
                    elif len(chunk)%16 != 0:
                        chunk += b' ' * (16 - (len(chunk) % 16))
                    outfile.write(encryptor.encrypt(chunk))
    def _decrypt(self, key, filename):
        chunksize = 64 * 1024
        outputFile = filename[:-4]
        with open(filename, 'rb') as infile:
            filesize = int(infile.read(16))
            IV = infile.read(16)
            decryptor = AES.new(key, AES.MODE_CBC, IV)
            with open(outputFile, 'wb') as outfile:
                while True:
                    chunk = infile.read(self.chunksize)
                    if len(chunk) == 0:
                        break
                    outfile.write(decryptor.decrypt(chunk))
                    outfile.truncate(filesize)
    
    # only called once as server start
    def _load(self):
        if not os.path.isfile('./' + settings.USER_BOOK_FILE + '.aes'):
            logger.debug('no user book existed')
            return
        try:
            self._decrypt(self._getKey(self.password), settings.USER_BOOK_FILE + '.aes')
            with open(settings.USER_BOOK_FILE, 'r') as j_file:
                data = json.load(j_file)
                for k,v in data.items():
                    self.users.append(User(k, v))
        except Exception as e:
            logger.error(f'load user book error: {e}')
            # if decry fail. rename the old one and create an new user book
            os.rename(settings.USER_BOOK_FILE + '.aes', settings.USER_BOOK_FILE + '_old' + '.aes')
        else:
            logger.debug('user book loaded')
        finally:
            self.updated = True
    
    async def store(self):
        while True:
            if self.updated:
                await asyncio.sleep(3)
            else:
                d = {}
                for u in self.users:
                    d[u.name] = u.password
                try:
                    with open(settings.USER_BOOK_FILE, 'w') as j_file:
                        json.dump(d, j_file)
                    self._encrypt(self._getKey(self.password), settings.USER_BOOK_FILE)
                except Exception as e:
                    logger.error(f'update user book error: {e}')
                else:
                    logger.debug('user book updated')
                finally:
                    os.remove('./' + settings.USER_BOOK_FILE)
                    self.updated = True
    
    def register(self, name, pw):
        if len(self.users) < settings.RESISTERED_USER_MAX_AMOUNT:
            self.users.append(User(name, pw))
            logger.info(f'User {name} done registered.')
            if settings.DEBUG:
                l = ''
                for u in self.users:
                    l += (u.name + ',')
                logger.debug(f'all user: {l}')
            self.updated = False
            return self.users[-1]
        else:
            logging.error('Reach max registerred user')
            return None
    def unregister(self, name):
        for i in range(len(self.users)):
            if self.users[i].name == name:
                del self.users[i]
                self.updated = False
                break
        if settings.DEBUG:
            l = ''
            for u in self.users:
                l += (u.name + ',')
            logger.debug(f'all user: {l}')
    def isUsableName(self, name):
        if len(name) > settings.ALLOWED_LEN_FOR_NAME:
            return False
        for c in name:
            if c not in settings.ALLOWED_CHAR_FOR_NAME:
                return False
        for u in self.users:
            if u.name == name:
                return False
        return True
    def isUsablePW(self, pw):
        if len(pw) > settings.ALLOWED_LEN_FOR_PASSWORD_MAX \
            or len(pw) < settings.ALLOWED_LEN_FOR_PASSWORD_MIN:
            return False
        for c in pw:
            if c not in settings.ALLOWED_CHAR_FOR_PASSWORD:
                return False
        return True
    def getValidRegisteredUser(self, name, pw):
        for u in self.users:
            if u.name == name and u.password == pw:
                return u
        return None
    def getObjectByName(self, name):
        for u in self.users:
            if u.name == name:
                return u
        return None

class ChatRoom:
    def __init__(self, pw):
        self.online_users = {}  # map websocket object to User object
        self.msg_buffer = [None for _ in range(settings.MSG_BUFFER_MAX_AMOUNT)]
        self.last_msg = 0
        self.user_book = UserBook(pw)
    
    def addMsg(self, user_name, msg):
        if self.last_msg == settings.MSG_BUFFER_MAX_AMOUNT-1:
            self.last_msg = 0
        else:
            self.last_msg += 1
        self.msg_buffer[self.last_msg] = [user_name, msg]
    def getLastMsg(self):
        return self.msg_buffer[self.last_msg]
    def isValidMsg(self, msg):
        # TODO:
        return True
    
    def getUserNameByWS(self, websocket):
        if websocket in self.online_users:
            return self.online_users[websocket].name
        else:
            return None
    
    def constructMsgEvent(self):
        msg = self.msg_buffer[self.last_msg]
        return json.dumps( \
                {settings.JSON_KEY_ACTION: settings.JSON_VALUE_ACTION_TYPE_BROADCAST, \
                 settings.JSON_KEY_TYPE: settings.JSON_VALYE_TYPE_TYPE_MESSAGE, \
                 settings.JSON_KEY_NAME: msg[0], \
                 settings.JSON_KEY_MSG: msg[1]})
    def constructUserEvent(self, name, join):
        if join:
            return json.dumps( \
                {settings.JSON_KEY_ACTION:settings.JSON_VALUE_ACTION_TYPE_BROADCAST, \
                 settings.JSON_KEY_TYPE: settings.JSON_VALYE_TYPE_TYPE_USER, \
                 settings.JSON_KEY_NAME: name, \
                 settings.JSON_KEY_MSG: settings.JSON_VALUE_MSG_JOIN})
        else:
            return json.dumps( \
                {settings.JSON_KEY_ACTION:settings.JSON_VALUE_ACTION_TYPE_BROADCAST, \
                 settings.JSON_KEY_TYPE: settings.JSON_VALYE_TYPE_TYPE_USER, \
                 settings.JSON_KEY_NAME: name, \
                 settings.JSON_KEY_MSG: settings.JSON_VALUE_MSG_LEFT})
    
    def constructErrorMsg(self, req, err):
        return json.dumps(
                {settings.JSON_KEY_ACTION:settings.JSON_VALUE_ACTION_TYPE_RESPONSE, \
                 settings.JSON_KEY_REQUEST: req, \
                 settings.JSON_KEY_ERR: err})
    def constructSuccessMsg(self, req):
        return json.dumps(
                {settings.JSON_KEY_ACTION:settings.JSON_VALUE_ACTION_TYPE_RESPONSE, \
                 settings.JSON_KEY_REQUEST: req, \
                 settings.JSON_KEY_ERR: settings.ERROR_NONE})
    
    async def notifyNewMsg(self):
        if self.online_users:  # asyncio.wait doesn't accept an empty list
            message = self.constructMsgEvent()
            # asyncio.wait() by default set as return only if all tasks have been done.
            # await here allow notification to different client can be interrupted.
            # It implies when an user type the msg, corresponding coroutin for
            #  his websocket will handle his next msg only after braodcast done
            #  and the broadcast task itself is async can be interrupted by another task
            await asyncio.wait([user.send(message) for user in self.online_users])
    async def notifyUsersStateChange(self, name, join):
        if self.online_users:  # asyncio.wait doesn't accept an empty list
            message = self.constructUserEvent(name, join)
            await asyncio.wait([user.send(message) for user in self.online_users])
    
    # called only if the user has been registered.
    # for modifying self.online_user only, not for modifying user_book
    async def addOnlineUser(self, websocket, user):
        self.online_users[websocket] = user
        await self.notifyUsersStateChange(user.name, True)
        if settings.DEBUG:
            l = ''
            for k,v in self.online_users.items():
                l += (v.name + ',')
            logger.debug(f'current online users({len(self.online_users)}): {l}',)
    async def removeOnlineUser(self, websocket):
        name = self.getUserNameByWS(websocket)
        if name != None:
            del self.online_users[websocket]
            await self.notifyUsersStateChange(name, False)
        if settings.DEBUG:
            l = ''
            for k,v in self.online_users.items():
                l += (v.name + ',')
            logger.debug(f'current online users({len(self.online_users)}): {l}',)

    # everytime when a client connect to this socket, getRequest enter once
    async def handleRequest(self, websocket, path):
        try:
            # a websocket is stand for a single user
            # TODO: send the initial state to the new-coming user
            if settings.DEBUG:
                await websocket.send('hi from server')
                logger.debug('sent initial state to client')
            
            # async loop here to check whenever there is msg from 'the' user
            async for message in websocket:
                
                logger.debug(f'got msg: {message} from {websocket}')
                data = json.loads(message)
                
                ### user typed message ###
                if data[settings.JSON_KEY_REQUEST] == settings.JSON_VALUE_REQUEST_TYPE_MSG:
                    if len(data[settings.JSON_KEY_MSG])<0:
                        res = self.constructErrorMsg(data[settings.JSON_KEY_REQUEST], \
                                                     settings.ERROR_INVALID_MSG)
                        logging.error(f'invalid msg: {data}')
                        await asyncio.wait([websocket.send(res)])
                    elif not self.isValidMsg(data['msg']):
                        res = self.constructErrorMsg(data[settings.JSON_KEY_REQUEST], \
                                                     settings.ERROR_ILLIGAL_MSG)
                        logging.debug(f'illigal msg: {data}')
                        await asyncio.wait([websocket.send(res)])
                    else:
                        msg = data[settings.JSON_KEY_MSG]
                        if len(msg) > settings.MAX_MSG_LEN:
                            msg = msg[0:settings.MAX_MSG_LEN]
                        self.addMsg(self.getUserNameByWS(websocket), msg)
                        await self.notifyNewMsg()
                
                ### login ###
                elif data[settings.JSON_KEY_REQUEST] == settings.JSON_VALUE_REQUEST_TYPE_LOGIN:
                    if len(data[settings.JSON_KEY_NAME])<0 or len(data[settings.JSON_KEY_PASSWORD])<0:
                        res = self.constructErrorMsg(data[settings.JSON_KEY_REQUEST], \
                                                     settings.ERROR_INVALID_LOGIN)
                        logging.error(f'invalid name/pw when login: {data}')
                        await asyncio.wait([websocket.send(res)])
                    elif len(self.online_users) >= settings.ONLINE_USER_MAX_AMOUNT:
                        # websockets itself doesn't have limitation on # of connections
                        res = self.constructErrorMsg(data[settings.JSON_KEY_REQUEST], \
                                                     settings.ERROR_TOO_MANY_ONLINE_USER)
                        logging.error(f'reach max online user')
                        await asyncio.wait([websocket.send(res)])
                    else:
                        u = self.user_book.getValidRegisteredUser(data[settings.JSON_KEY_NAME], data[settings.JSON_KEY_PASSWORD])
                        if u != None:
                            await self.addOnlineUser(websocket, u)
                            res = self.constructSuccessMsg(data[settings.JSON_KEY_REQUEST])
                            await asyncio.wait([websocket.send(res)])
                        else:
                            res = self.constructErrorMsg(data[settings.JSON_KEY_REQUEST], \
                                                         settings.ERROR_WRONG_LOGIN_IDENTITY)
                            logging.debug(f'wrong name/pw when login: {data}')
                            await asyncio.wait([websocket.send(res)])
                            
                # TODO: logout
                
                ### register ###
                # wonn't lead to auto login
                elif data[settings.JSON_KEY_REQUEST] == settings.JSON_VALUE_REQUEST_TYPE_REG:
                    if len(data[settings.JSON_KEY_NAME]) < 0 \
                        or len(data[settings.JSON_KEY_PASSWORD]) < 0:
                        res = self.constructErrorMsg( \
                                settings.JSON_VALUE_REQUEST_TYPE_REG, \
                                settings.ERROR_INVALID_REG_REQ)
                        logging.error(f'invalid reg req: {data}')
                        await asyncio.wait([websocket.send(res)])
                    elif len(self.user_book.users) >= settings.RESISTERED_USER_MAX_AMOUNT:
                        res = self.constructErrorMsg(data[settings.JSON_KEY_REQUEST], \
                                                     settings.ERROR_TOO_MANY_ONLINE_USER)
                        logging.error(f'reach max online user')
                        await asyncio.wait([websocket.send(res)])
                    elif not self.user_book.isUsableName(data[settings.JSON_KEY_NAME]):
                        res = self.constructErrorMsg( \
                                settings.JSON_VALUE_REQUEST_TYPE_REG, \
                                settings.ERROR_INVALID_REG_NAME)
                        logging.debug(f'invalid reg name: {data}')
                        await asyncio.wait([websocket.send(res)])
                    elif not self.user_book.isUsablePW(data[settings.JSON_KEY_PASSWORD]):
                        res = self.constructErrorMsg( \
                                settings.JSON_VALUE_REQUEST_TYPE_REG, \
                                settings.ERROR_INVALID_REG_PW)
                        logging.debug(f'invalid reg pw: {data}')
                        await asyncio.wait([websocket.send(res)])
                    else:
                        u = self.user_book.register(data[settings.JSON_KEY_NAME], data[settings.JSON_KEY_PASSWORD])
                        if u != None:
                            res = self.constructSuccessMsg(settings.JSON_VALUE_REQUEST_TYPE_REG)
                        else:
                            res = self.constructErrorMsg( \
                                    settings.JSON_VALUE_REQUEST_TYPE_REG, \
                                    settings.ERROR_ERROR)
                        await asyncio.wait([websocket.send(res)])
                
                ### unregister ###
                elif data[settings.JSON_KEY_REQUEST] == settings.JSON_VALUE_REQUEST_TYPE_UNREG:
                    if len(data[settings.JSON_KEY_NAME]) < 0:
                        res = self.constructErrorMsg( \
                                settings.JSON_VALUE_REQUEST_TYPE_UNREG, \
                                settings.ERROR_INVALID_UNREG_REQ)
                        logger.error(f'invalid unreg msg: {data}')
                        await asyncio.wait([websocket.send(res)])
                    else:
                        self.user_book.unregister(data[settings.JSON_KEY_NAME])
                        await self.removeOnlineUser(websocket)
                        res = self.constructSuccessMsg(settings.JSON_VALUE_REQUEST_TYPE_UNREG)
                        await asyncio.wait([websocket.send(res)])
                
                else:
                    logger.error(f'unsupported event: {data}')
        except Exception as e:
            logger.warning(f'reading socket terminated: {e}')
        finally:
            # enter when connection closed
            logger.error(f'websocket {websocket} disconnected!!')
            await self.removeOnlineUser(websocket)

#####

def serverMain(port=settings.DEFAULT_WSS_PORT):
    # TODO: support specified cert in cmd
    try:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        localhost_crt = pathlib.Path(__file__).with_name(settings.DEFAULT_SSL_CRT)
        localhost_key = pathlib.Path(__file__).with_name(settings.DEFAULT_SSL_KEY)
        ssl_context.load_cert_chain(localhost_crt, localhost_key)
    except Exception as e:
        logger.critical(f'load ssl context error:{e}')
        return
    else:
        logger.debug('ssl ready')
    
    try:
        start_server = websockets.serve(chat_room.handleRequest, 'localhost', port, ssl=ssl_context)
    except Exception as e:
        logger.error(f'websockets.serve error: {e}')
        return
    else:
        logger.warning('server started! waiting for connection from clients')
        print('server started!')

    tasks = [
        start_server,
        asyncio.ensure_future(chat_room.user_book.store())
    ]
    
    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    for p in needIncludePath:
        if p not in sys.path:
            sys.path.append(p)
    
    parser = argparse.ArgumentParser(description='Start a WSS Server.')
    parser.add_argument('-u', '--password', dest='user_book_pw', required=True, \
                        help='(required) password to encry/decry the user book file')
    parser.add_argument('-p', '--port', dest='port', \
                        help=f'start a wss server at localhost port. default set at {settings.DEFAULT_WSS_PORT}')
    parser.add_argument('-d', '--debug', dest='debug', type=int, \
                        help=f'number. enable debug log or not. (default) 0- disabled; 1- enabled. log file is {settings.LOG_FILE}; 2- enabled and print to stderr as well')
    args, unknown = parser.parse_known_args()
    
    # set logger
    logger = logging.getLogger()
    logging.basicConfig(filename=settings.LOG_FILE)
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
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)i - %(message)s')
    else:
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    from logging.handlers import RotatingFileHandler
    # TODO: test whether rotate actually work
    log_file_handler = RotatingFileHandler(settings.LOG_FILE, mode='a', \
                                     maxBytes=settings.MAX_LOG_SIZE*1024*1024, \
                                     backupCount=2, encoding=None, delay=0)
    log_file_handler.setFormatter(log_formatter)
    if settings.DEBUG and debug:
        logging.warning(f'debug mode')
        logger.setLevel(logging.DEBUG)
        log_file_handler.setLevel(logging.DEBUG)
        if args.debug and args.debug == 2:
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setLevel(logging.DEBUG)
            stderr_handler.setFormatter(log_formatter)
            logger.addHandler(stderr_handler)
    else:
        logging.warning(f'non debug mode')
        logger.setLevel(logging.WARNING)
        log_file_handler.setLevel(logging.WARNING)
    logger.addHandler(log_file_handler)
    
    if settings.DEBUG == False or settings.WS_MOD_LOG == False or debug == False:
        ws_logger = logging.getLogger('websockets')
        ws_logger.setLevel(logging.WARNING)
    
    logger.debug(f'python sys.path: {sys.path}')
    
    chat_room = ChatRoom(args.user_book_pw)
    
    # TODO: start a watchdog process
    
    # will then block the main thread
    if args.port:
        logging.debug(f'will start server at port {args.port}')
        serverMain(port=args.port)
    else:
        logging.debug(f'will start server at port {settings.DEFAULT_WSS_PORT}')
        serverMain()
