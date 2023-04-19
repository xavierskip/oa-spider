# from oa import *
import configparser
import argparse
import os
from .logger import logger_configure
from .oa import CONFIG

parser = argparse.ArgumentParser()
parser.add_argument("-c",help="config file",
                    type=str)
args = parser.parse_args()


def start_config():
    ini = configparser.ConfigParser()
    if args.c != None:
        # print(args.c, os.path.abspath(args.c))
        ini.read(os.path.abspath(args.c), encoding='utf-8')
    else:
        ini.read(CONFIG['INI'], encoding='utf-8')
    overwriteconfig_4logger(ini)  # 
    return ini

def overwriteconfig_4logger(ini):
    for k, v in ini.items('config'):
        CONFIG[k.upper()] = v
    logger_configure(ini)

OAini = start_config()