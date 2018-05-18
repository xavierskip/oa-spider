#!/usr/bin/env python
# coding: utf-8
import logging
import os
from g import CONFIG



# http://stackoverflow.com/a/8349076/1265727
class MyFormatter(logging.Formatter):
    """
    logger.error 详细记录
    logger.info  记录时间及信息
    logger.debug 记录信息
    """

    err_fmt = "[%(levelname)s] File \"%(pathname)s\", line %(lineno)d, in %(funcName)s\n%(msg)s"
    dbg_fmt = "%(msg)s"

    def __init__(self, fmt="[%(asctime)s] %(message)s"):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._fmt

        # Replace the original format with one customized by logging level
        if record.levelno > logging.INFO:
            self._fmt = MyFormatter.err_fmt

        elif record.levelno < logging.INFO:
            self._fmt = MyFormatter.dbg_fmt

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._fmt = format_orig

        return result


spiderlog = logging.getLogger('oa')
maillog = logging.getLogger('mail')

spiderlog.setLevel(logging.DEBUG)
maillog.setLevel(logging.DEBUG)


# wait for load config
def ready4log():
    fmt = MyFormatter()

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    spiderlog.addHandler(sh)

    if os.getenv('oa_spider') != 'debug':
        fh = logging.FileHandler(CONFIG['LOG_FILE'], encoding='utf-8')
        fh.setFormatter(fmt)
        spiderlog.addHandler(fh)

    mh = logging.FileHandler(CONFIG['MAILFILE'], mode='w', encoding='utf-8')
    mh.setFormatter(fmt)
    maillog.addHandler(mh)


def load_config(config):
    for k, v in config.items('config'):
        CONFIG[k.upper()] = v.decode('utf-8')
    ready4log()
