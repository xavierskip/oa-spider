from oa import *
from mylog import spiderlog, maillog, ready4log
import ConfigParser


def start_config():
    ini = ConfigParser.ConfigParser()
    ini.read(CONFIG['INI'])
    overwriteconfig_4logger(ini)  # 
    return ini

def overwriteconfig_4logger(ini):
    for k, v in ini.items('config'):
        CONFIG[k.upper()] = v.decode('utf-8')
    ready4log()

OA_ini = start_config()