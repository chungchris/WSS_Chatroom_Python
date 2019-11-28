#!/bin/python3

import asyncio
import json
import logging
import pathlib
import queue
import ssl
import sys
import tkinter as tk

#from collections import deque

import websockets

import settings

#####

logger = None
wss_client_connected = False

#####
    
'''
async def hello():
    uri = "wss://localhost:8766"
    # use 'with' to make a single-time job section 
    async with websockets.connect(
        uri, ssl=ssl_context
    ) as websocket:
        name = input("Sending your name? ")

        await websocket.send(name)
        #print(f"> {name}")

        greeting = await websocket.recv()
        print(f"< {greeting}")
'''

#####

class Command:
    def __init__(self, ws_q, res_q):
        self.ws_q = ws_q
        self.res_q = res_q
        
    async def send(self, msg):
        await self.ws_q.put(msg)
    
    async def checkResponse(self, req):
        while True:
            res = await self.res_q.get()
            self.res_q.task_done()
            # (data['request'], data['err'], data['msg'])
            if res[0] == req:
                return res[1]
    
    async def register(self, name, pw):
        await self.send(json.dumps( \
                {settings.JSON_KEY_REQUEST: settings.JSON_VALUE_REQUEST_TYPE_REG, \
                 settings.JSON_KEY_NAME: name, \
                 settings.JSON_KEY_PASSWORD: pw}))
        res = await asyncio.wait_for(self.checkResponse(settings.JSON_VALUE_REQUEST_TYPE_REG), \
                               timeout=settings.WAIT_FOR_RESPONSE_TOLERANCE)
        return res
    async def unregister(self, name):
        await self.send(json.dumps(
                {settings.JSON_KEY_REQUEST: settings.JSON_VALUE_REQUEST_TYPE_UNREG, \
                 settings.JSON_KEY_NAME: name}))
        res = await asyncio.wait_for(checkResponse(settings.JSON_VALUE_REQUEST_TYPE_UNREG), \
                               timeout=settings.WAIT_FOR_RESPONSE_TOLERANCE)
        return res
    async def login(self, name, pw):
        await self.send(json.dumps( \
                {settings.JSON_KEY_REQUEST: settings.JSON_VALUE_REQUEST_TYPE_LOGIN, \
                 settings.JSON_KEY_NAME: name, \
                 settings.JSON_KEY_PASSWORD: pw}))
        res = await asyncio.wait_for(self.checkResponse(settings.JSON_VALUE_REQUEST_TYPE_LOGIN), \
                               timeout=settings.WAIT_FOR_RESPONSE_TOLERANCE)
        return res
    async def sendMsg(self, msg):
        await self.send(json.dumps(
                {settings.JSON_KEY_REQUEST: settings.JSON_VALUE_REQUEST_TYPE_MSG, \
                 settings.JSON_KEY_MSG: msg}))
        # no response

#####

async def test(ws_q, res_q):
    '''
    count = 0
    while count<5:
        if stop_service:
            break
        
        await queue.put(1)
        eprint('put item in q')
        count += 1
        await asyncio.sleep(5)
    '''
    tester = Command(ws_q, res_q)
    await asyncio.sleep(2)
    
    if args.user_name:
        name = args.user_name
    else:
        name = 'chris'
    err = await tester.register(name, '5566')
    logger.debug(f'testRegister ({name}, 5566): {err}')
    await asyncio.sleep(1)
    err = await tester.login(name, '5566')
    logger.debug(f'testLogin ({name}, 5566): {err}')
    await asyncio.sleep(1)
    
    # test send msg
    for i in range(5):
        sent = str(i)*10
        await tester.sendMsg(sent)
        await asyncio.sleep(1)

#####

# get cmd from sync cmd_q in which cmds are from gui thread
# translate to request and put into asyn ws_q
# ws_q will be processed by another coroutin to send req to ws
# this coroutin is expected to in the daemon thread of main thread,
#   so should be ok no self stop way designed so far
async def processCommandFromGUI(cmd_q, ws_q, res_q, loop, user):
    handler = Command(ws_q, res_q)
    while True:
        try:
            #logger.debug(f'non block get from cmd_q')
            cmd = cmd_q.get_nowait()
            logger.debug('unblock')
        except queue.Empty:
            #logger.debug('no cmd, sleep 0.5s')
            await asyncio.sleep(0.5)
            continue
        except Exception as e:
            logger.error(f'read cmd_q error: {e}')
            break
        else:
            logger.debug(f'got cmd:{cmd}')
            logger.debug(f'original status:{user.status}')
            # the event handlers in GUI thread is in charge of making sure 
            #   not sending unnecessary/illigal cmds.
            if cmd[0] == settings.JSON_VALUE_REQUEST_TYPE_MSG:
                await handler.sendMsg(cmd[1])
            elif cmd[0] == settings.JSON_VALUE_REQUEST_TYPE_LOGIN:
                err = await handler.login(cmd[1], cmd[2])
                if err == settings.ERROR_NONE:
                    user.status = settings.USER_STATE_LOGIN
                    user.name = cmd[1]
                    user.ui_status_label_text.set(settings.UI_STATUS_MSG_LOGIN)
                    user.ui_status_label_color('blue')
                elif err == settings.ERROR_WRONG_LOGIN_IDENTITY:
                    user.ui_status_label_text.set(settings.UI_STATUS_MSG_INVALID_LOGIN)
                    user.ui_status_label_color('red')
                else:
                    user.ui_status_label_text.set(settings.UI_STATUS_MSG_ERROR)
                    user.ui_status_label_color('red')
            elif cmd[0] == settings.JSON_VALUE_REQUEST_TYPE_REG:
                err = await handler.register(cmd[1], cmd[2])
                logger.debug(f'!!!!err:{err}')
                if err == settings.ERROR_NONE:
                    logger.debug(f'ttttt')
                    user.status = settings.USER_STATE_INITIAL
                    user.ui_status_label_text.set(settings.UI_STATUS_MSG_REG_DONE)
                    user.ui_status_label_color('blue')
                elif err == settings.ERROR_INVALID_REG_NAME:
                    user.ui_status_label_text.set(settings.UI_STATUS_MSG_INVALID_REG_NAME)
                    user.ui_status_label_color('red')
                elif err == settings.ERROR_INVALID_REG_PW:
                    user.ui_status_label_text.set(settings.UI_STATUS_MSG_INVALID_REG_PW)
                    user.ui_status_label_color('red')
                else:
                    user.ui_status_label_text.set(settings.UI_STATUS_MSG_ERROR)
                    user.ui_status_label_color('red')
            elif cmd[0] == settings.JSON_VALUE_REQUEST_TYPE_UNREG:
                err = await handler.unregister(cmd[1])
                if err == settings.ERROR_NONE:
                    user.status = settings.USER_STATE_INITIAL
                    user.ui_status_label_text.set(settings.UI_STATUS_MSG_INITIAL)
                    user.ui_status_label_color('black')
                else:
                    user.ui_status_label_text.set(settings.UI_STATUS_MSG_ERROR)
                    user.ui_status_label_color('red')
            else:
                loggert.error('unsupported cmd')

# deque msg from q and put into websocket
async def pushMsgToWS(ws_q, websocket):
    # Get a "work item" out of the queue.
    while True:
        msg = await ws_q.get()
        await websocket.send(msg)
        logger.info(f'sent to ws: {msg}')
        ws_q.task_done()

# wait for there is any msh dent from server
async def getMsgFromWS(websocket, res_q, user=None):
    try:
        async for message in websocket:
            logger.info(f'got from ws: {message}')
            try:
                data = json.loads(message)
                if data[settings.JSON_KEY_ACTION] \
                        == settings.JSON_VALUE_ACTION_TYPE_RESPONSE:
                    res_q.put_nowait((data[settings.JSON_KEY_REQUEST], \
                                      data[settings.JSON_KEY_ERR]))
                    # TODO: exception for q full
                elif data[settings.JSON_KEY_ACTION] \
                        == settings.JSON_VALUE_ACTION_TYPE_BROADCAST:
                    if user != None:
                        if data[settings.JSON_KEY_TYPE] \
                                == settings.JSON_VALYE_TYPE_TYPE_MESSAGE:
                            msg = data[settings.JSON_KEY_NAME] + ': ' + data[settings.JSON_KEY_MSG]
                            user.ui_room.insert(tk.END, f'{msg}\n')
                        elif data[settings.JSON_KEY_TYPE] \
                                == settings.JSON_VALYE_TYPE_TYPE_USER:
                            msg = '--- User \'' + data[settings.JSON_KEY_NAME] + '\' ' \
                                    + data[settings.JSON_KEY_MSG] + ' ---'
                            user.ui_room.insert(tk.END, f'{msg}\n')
                else:
                    logger.error(f'unsupport msg:{data}')
            except Exception as e:
                logger.error(f'unexpect msg:{message}. e:{e}')
    except:
        a, b, c = sys.exc_info()
        logger.warning(f'exception occured on reading msg from websocket...')
        logger.warning(a)
        logger.warning(b)
        logger.warning(c)
    finally:
        logger.warning('server disconnected')
        global wss_client_connected
        wss_client_connected = False

# will start coroutins after connect to server
#  coroutin pushMsgToWS: get msg from ws_q and put into ws
#  coroutin getMsgFromWS: get msg from ws and put into res_q
#  coroutin processCommandFromGUI: get msg from cmd_q and put into ws_q
async def connect(ssl_context, ws_q, res_q, \
                  host=settings.DEFAULT_WSS_HOST, \
                  port=settings.DEFAULT_WSS_PORT,
                  cmd_q=None, loop=None, o=None):
    uri = host + ':' + str(port)
    async with websockets.connect(
        uri, ssl=ssl_context
    ) as websocket:
        logger.warning('server connected')
        
        # Create a worker task to process the queue
        task1 = asyncio.create_task(pushMsgToWS(ws_q, websocket))
        
        if __name__ == "__main__":
            task2 = asyncio.create_task(getMsgFromWS(websocket, res_q))
            task3 = asyncio.create_task(test(ws_q, res_q))
            tasks = [task1, task2, task3]
        else:
            task2 = asyncio.create_task(getMsgFromWS(websocket, res_q, user=o))
            task3 = asyncio.create_task(processCommandFromGUI(cmd_q, ws_q, res_q, loop, o))
            # TODO: task4 to pass update to gui. maybe needless
            tasks = [task1, task2, task3]
        
        global wss_client_connected
        wss_client_connected = True
        
        # Wait until the queue is fully processed.
        #await queue.join()
        #eprint('the q has been fully processed')
        
        # Cancel our worker tasks.
        #for task in tasks:
        #    task.cancel()
        
        logger.debug('coroutin created')
        await asyncio.wait(tasks)

#####

# this func can entered by this module itself, 
#   or through Client() object allocated by another module
def clientMain(mod_logger=None, cmd_q=None, o=None):
    if mod_logger != None:
        global logger
        logger = mod_logger
    
    # set SSL context
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    localhost_crt = pathlib.Path(__file__).with_name(settings.DEFAULT_SSL_CRT)
    ssl_context.load_verify_locations(localhost_crt)
    logger.debug('ssl ready')
    
    # start wss client
    if __name__ == "__main__":
        loop = asyncio.get_event_loop()
    else:
        logger.debug('create event loop')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    ws_q = asyncio.Queue(maxsize=settings.WS_Q_SIZE)
    res_q = asyncio.Queue(maxsize=settings.RESPONSE_Q_SIZE)
    #bc_q = asyncio.Queue(maxsize=settings.BROADCAST_Q_SIZE)
    
    if __name__ == "__main__":
        loop.run_until_complete( \
                              connect(ssl_context, ws_q, res_q))
    else:
        # default asyncio event loop policy only automatically creates 
        #   event loops in the main threads. Other threads must create 
        #   event loops expliciy.
        # here we assumed that is this func not entered from main,
        #   it's not on main thread
        loop.run_until_complete( \
                              connect(ssl_context, ws_q, res_q, \
                                      cmd_q=cmd_q, loop=loop, o=o))

class Client:
    def __init__(self, logger=None):
        self.logger = logging.getLogger(__name__)
        self.status = settings.USER_STATE_INITIAL
        self.ui_status_label_text = None
        self.ui_status_label_color = None
        self.ui_room = None
        self.name = ''
        if settings.DEBUG == False or settings.WS_MOD_LOG == False:
            ws_logger = logging.getLogger('websockets')
            ws_logger.setLevel(logging.WARNING)
    
    def startFromGUI(self, cmd_q, \
                     obj_chat_room, status_label_text, status_label_color):
        self.ui_status_label_text = status_label_text
        self.ui_status_label_color = status_label_color
        self.ui_room = obj_chat_room
        clientMain(mod_logger=self.logger, cmd_q=cmd_q, o=self)

#####

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Start a WSS Client.')
    parser.add_argument('-u', '--user-name', dest='user_name', help='start a wss client with name')
    args, unknown = parser.parse_known_args()
    
    # set logger
    logger = logging.getLogger()
    logging.basicConfig(filename=settings.LOG_FILE)
    if settings.DEBUG:
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
        
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.DEBUG)
        stderr_handler.setFormatter(log_formatter)
        logger.addHandler(stderr_handler)
    else:
        logger.setLevel(logging.WARNING)
        my_handler.setLevel(logging.WARNING)
    logger.addHandler(log_file_handler)
    
    if settings.DEBUG == False or settings.WS_MOD_LOG == False:
        ws_logger = logging.getLogger('websockets')
        ws_logger.setLevel(logging.WARNING)

    # start client    
    clientMain()
