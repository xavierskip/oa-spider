from oa import *
from logger import logger_configure
import ConfigParser
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("-c", help="config file",
                    type=str)
args = parser.parse_args()


def start_config():
    ini = ConfigParser.ConfigParser()
    if args.c != None:
        # print(args.c, os.path.abspath(args.c))
        ini.read(os.path.abspath(args.c))
    else:
        ini.read(CONFIG['INI'])
    overwriteconfig_4logger(ini)  # 
    return ini

def overwriteconfig_4logger(ini):
    for k, v in ini.items('config'):
        CONFIG[k.upper()] = v.decode('utf-8')
    logger_configure(ini)

OAini = start_config()