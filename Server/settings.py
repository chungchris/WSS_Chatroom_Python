#!/bin/python3
# -*- coding: utf-8 -*-

# DEBUG
DEBUG = True
WS_MOD_LOG = False

# SERVER CONFIG
DEFAULT_WSS_PORT = 8766

# LOG
LOG_FILE = 'server.log'
MAX_LOG_SIZE = 64 #(MB)

# SSL
DEFAULT_SSL_CRT = 'server.crt'
DEFAULT_SSL_KEY = 'server.key'

# MESSAGE
MAX_MSG_LEN = 1024
MSG_BUFFER_MAX_AMOUNT = 1024

# USERS
RESISTERED_USER_MAX_AMOUNT = 1000
ONLINE_USER_MAX_AMOUNT = 100
USER_BOOK_FILE = 'user_book'

# UX
ALLOWED_CHAR_FOR_NAME = set(['A','B','C','D','E','F','G','H','I','J','K','L', \
                            'M','N','O','P','Q','R','S','T','U','V','W','X', \
                            'Y','Z',' ','-','_','a','b','c','d','e','f','g', \
                            'h','i','j','k','l','m','n','o','p','q','r','s', \
                            't','u','v','w','x','y','z'])
ALLOWED_LEN_FOR_NAME = 32
ALLOWED_CHAR_FOR_PASSWORD = set(['A','B','C','D','E','F','G','H','I','J','K', \
                                'L','M','N','O','P','Q','R','S','T','U','V', \
                                'W','X','Y','Z','a','b','c','d','e','f','g', \
                                'h','i','j','k','l','m','n','o','p','q','r', \
                                's','t','u','v','w','x','y','z','0','1','2', \
                                '3','4','5','6','7','8','9'])
ALLOWED_LEN_FOR_PASSWORD_MIN = 4
ALLOWED_LEN_FOR_PASSWORD_MAX = 16

# MSG B/T SERVER/CLIENT
JSON_KEY_REQUEST = 'request'
JSON_VALUE_REQUEST_TYPE_MSG = 'msg'
JSON_VALUE_REQUEST_TYPE_LOGIN = 'login'
JSON_VALUE_REQUEST_TYPE_REG = 'reg'
JSON_VALUE_REQUEST_TYPE_UNREG = 'unreg'
JSON_KEY_MSG = 'msg'
JSON_VALUE_MSG_JOIN = 'join'
JSON_VALUE_MSG_LEFT = 'left'
JSON_KEY_NAME = 'name'
JSON_KEY_PASSWORD = 'password'
JSON_KEY_ACTION = 'action'
JSON_VALUE_ACTION_TYPE_BROADCAST = 'broadcast'
JSON_VALUE_ACTION_TYPE_RESPONSE = 'response'
JSON_KEY_TYPE = 'type'
JSON_VALYE_TYPE_TYPE_MESSAGE = 'msg'
JSON_VALYE_TYPE_TYPE_USER = 'user'
JSON_KEY_ERR = 'err'

# ERROR MSG
## ERROR MSG TO CLIENT
ERROR_NONE = 0
ERROR_ERROR = -1
ERROR_INVALID_MSG = -2
ERROR_ILLIGAL_MSG = -3
ERROR_INVALID_LOGIN = -4
ERROR_WRONG_LOGIN_IDENTITY = -5
ERROR_INVALID_UNREG_REQ = -6
ERROR_INVALID_REG_REQ = -7
ERROR_INVALID_REG_NAME = -8
ERROR_INVALID_REG_PW = -9
ERROR_TOO_MANY_ONLINE_USER = -10
ERROR_TOO_MANY_REGISTER_USER = -11

