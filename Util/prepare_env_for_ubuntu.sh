#!/bin/bash

sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.7
python3.7 -V
sudo apt install python3-pip

sudo apt-get install python3.7-tk
sudo apt-get install -f

sudo apt install git

sudo python3.7 -m pip install websockets
#sudo python3.7 -m pip uninstall crypto
#sudo python3.7 -m pip uninstall pycryptodome
sudo python3.7 -m pip install pycryptodome
