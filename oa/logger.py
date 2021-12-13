#!/usr/bin/env python
# coding: utf-8

import os
from g import CONFIG
import logging
from logging.handlers import SMTPHandler, TimedRotatingFileHandler


class mimetypeSMTPHandler(SMTPHandler):
    def set_mimetype(self, mimetype):
        self.mimetype = mimetype

    def emit(self, record):
        """
        Emit a record.
        Format the record and send it to the specified addressees.
        """
        try:
            import smtplib
            from email.header import Header
            from email.utils import formatdate
            from email.mime.text import MIMEText
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            try:
                minetype = self.mimetype
            except AttributeError:
                minetype = 'plain'
            smtp = smtplib.SMTP(self.mailhost, port, timeout=self._timeout)
            msg = self.format(record)
            msg = MIMEText(msg, minetype, 'utf-8')
            msg['Subject'] = Header(self.getSubject(record), 'utf-8')
            msg['From'] = self.fromaddr
            msg['To'] = ','.join(self.toaddrs)
            msg['Date'] = formatdate()
            if self.username:
                if self.secure is not None:
                    smtp.ehlo()
                    smtp.starttls(*self.secure)
                    smtp.ehlo()
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg.as_string())
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        # except:
        #     self.handleError(record)

# http://stackoverflow.com/a/8349076/1265727
class MyFormatter(logging.Formatter):
    """
    logger.error 详细记录
    logger.info  记录时间及信息
    logger.debug 记录信息

    Level   Numeric value
    CRITICAL    50
    ERROR   40
    WARNING 30
    INFO    20
    DEBUG   10
    NOTSET  0
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

# http://ju.outofmemory.cn/entry/85917
# sh.setFormatter(EncodingFormatter('%(message)s', encoding='utf-8'))
class EncodingFormatter(logging.Formatter):
    def __init__(self, fmt, datefmt=None, encoding=None):
        logging.Formatter.__init__(self, fmt, datefmt)
        self.encoding = encoding
    def format(self, record):
        result = logging.Formatter.format(self, record)
        if isinstance(result, unicode):
            result = result.encode(self.encoding or 'utf-8')
        # for send mail
        if record.levelno >= logging.ERROR:
            result = "<pre>%s</pre>" %result
        return result

fmt = MyFormatter()
utf8fmt = EncodingFormatter('%(message)s', encoding='utf-8')

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
        fh = TimedRotatingFileHandler(CONFIG['LOG_FILE'],
            when='D', interval=30, encoding='utf-8')
        fh.setLevel(logging.INFO)
        fh.setFormatter(fmt)
        spiderloger.addHandler(fh)

    if not ini.has_section('mail'):
        return
    # do something ready for send email
    smtp = mimetypeSMTPHandler(
        ini.get('mail', 'host'),
        ini.get('mail', 'account'),
        ini.get('mail', 'address').split(','),
        "[WARNING]oa-spider",
        credentials=(ini.get('mail', 'account'), ini.get('mail', 'passwd')),
        )
    smtp.setLevel(logging.WARNING)
    smtp.setFormatter(utf8fmt)
    smtp.set_mimetype('html')
    spiderloger.addHandler(smtp)

    #mailoger
    mail = mimetypeSMTPHandler(
        ini.get('mail', 'host'),
        ini.get('mail', 'account'),
        ini.get('mail', 'address').split(','),
        ini.get('mail', 'subject'),
        credentials=(ini.get('mail', 'account'), ini.get('mail', 'passwd')),
        )
    mail.setLevel(logging.INFO)
    mail.setFormatter(utf8fmt)
    mail.set_mimetype('html')
    mailoger.addHandler(mail)

    