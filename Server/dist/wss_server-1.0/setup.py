#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 10:23:07 2019

@author: chungchris
"""

from setuptools import setup, find_packages

setup(
    name = "wss_server",
    version = "1.0",
    py_modules = ['wss_server', 'settings'],
    keywords = ("wss"),
    description = "WSS Chatroom Server",
    license = "GPLv3",
    
    url = "https://github.com/chungchris/WSS_Chatroom_Python",
    author = "Chris-PY Chung",
    author_email = "imchungchris@hotmail.com",
    
    #packages = find_packages(),
    #package_data = {},
    #include_package_data = True,
    data_files = [('', ['server.key', 'server.crt'])],
    platforms = "any",
    python_requires=">=3.6.1",
    install_requires = [
            "websockets>=8.1"],  
    
    scripts = [],
    entry_points = {
        'console_scripts': [
            'wss_chat_room_server = wss_chat_room_server:main'
        ]
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
    ],
)
