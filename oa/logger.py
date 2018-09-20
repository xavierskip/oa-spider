#!/usr/bin/env python
# coding: utf-8
from g import CONFIG
import logging
import logging.handlers
import os


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

fmt = MyFormatter()

spiderloger = logging.getLogger('oa')
spiderloger.setLevel(logging.DEBUG)
mailoger    = logging.getLogger('mail')
mailoger.setLevel(logging.DEBUG)

# wait __init__ to load config
def logger_configure(ini):
    # spiderloger
    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(fmt)
    spiderloger.addHandler(sh)

    if os.getenv('oa_spider') != 'debug':
        fh = logging.FileHandler(CONFIG['LOG_FILE'], encoding='utf-8')
        sh.setLevel(logging.INFO)
        fh.setFormatter(fmt)
        spiderloger.addHandler(fh)

    smtp = logging.handlers.SMTPHandler(
        ini.get('mail', 'host'),
        ini.get('mail', 'account'),
        ini.get('mail', 'address').split(','),
        "[WARNING]oa-spider",
        credentials=(ini.get('mail', 'account'), ini.get('mail', 'passwd')),
        )
    smtp.setLevel(logging.WARNING)
    spiderloger.addHandler(smtp)

    #mailoger
    mail = logging.handlers.SMTPHandler(
        ini.get('mail', 'host'),
        ini.get('mail', 'account'),
        ini.get('mail', 'address').split(','),
        ini.get('mail', 'subject'),
        credentials=(ini.get('mail', 'account'), ini.get('mail', 'passwd')),
        )
    mail.setLevel(logging.INFO)
    mailoger.addHandler(mail)

    