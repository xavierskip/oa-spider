#!/usr/bin/env python
# coding: utf-8
import os
import time
from oa import OAini
from oa.oa import  JZWJW_ZW, HBCDC_wui, JZWJW_wui,HBWJW
from oa.exceptions import LoginFailError, VPNdisconnect
from oa.logger import spiderloger, mailoger
from oa.notification import get_mail_digest
from oa.network import check_hbwjw_vpn
from requests.exceptions import ReadTimeout, ConnectionError
from smtplib import SMTPException, SMTPAuthenticationError, SMTPServerDisconnected

def try2try(trytimes, sleeptime=10):
    def _try(func):
        def wrapper(*args, **kwargs):
            # default TIMEOUT = 10
            # loop time interval 
            # 1 sleep
            # 2 TIMEOUT + sleeptime
            # 3 TIMEOUT + sleeptime
            # ....
            for _ in range(trytimes):
                try:
                    func(*args, **kwargs)
                    break
                except (ReadTimeout, ConnectionError) as e:
                    if _+1 == trytimes:
                        spiderloger.error(e, exc_info=True)
                        break
                    else:
                        spiderloger.info("%d %s try fail" %(_+1, func))
                        time.sleep(sleeptime)
                        continue
                except VPNdisconnect:
                    spiderloger.error("VPN disconnect.", exc_info=True)
                    break
                except LoginFailError:
                    # loginfail logging in oa.py
                    break
        return wrapper
    return _try

@try2try(3)
def hbcdc_do(ini):
    u, p = ini.get('hbcdc', 'user'), ini.get('hbcdc', 'passwd')
    hbcdc = HBCDC_wui(u, p)
    # hbcdc.do(unread=0, limit=5)
    hbcdc.do()

@try2try(3)
def jzwjw_do(ini):
    u, p = ini.get('jzwjw', 'user'), ini.get('jzwjw', 'passwd')
    jzwjw = JZWJW_wui(u, p)
    # jzwjw.do(unread=0)
    jzwjw.do()

@try2try(3)
def wjwzw_do(ini):
    u, p = ini.get('wjwzw', 'user'), ini.get('wjwzw', 'passwd')
    jzwjw = JZWJW_ZW(u, p)
    # jzwjw.do(unread=0, range=[0,4])
    jzwjw.do()

@try2try(3, 30)
def hbwjw_do(ini):
    if check_hbwjw_vpn():
        u, p = ini.get('hbwjw', 'user'), ini.get('hbwjw', 'passwd')
        hbwjw = HBWJW(u, p)
        hbwjw.do()
    else:
        raise VPNdisconnect

def main(ini):
    """
    catch ReadTimeout error for website is down
    """
    if ini.has_option('jzwjw', 'user'):
        jzwjw_do(ini)
    if ini.has_option('wjwzw', 'user'):
        wjwzw_do(ini)
    if ini.has_option('hbcdc', 'user'):
        hbcdc_do(ini)
    if ini.has_option('hbwjw', 'user'):
        hbwjw_do(ini)

    if ini.has_section('mail'):
        digest = get_mail_digest()
        return digest
    else:
        return None


if __name__ == '__main__':
    try:
        digest = main(OAini)
        if digest:
            step = 0
            while step < 3:
                try:
                    spiderloger.info(u'...发送中...%s...' % (step + 1))
                    mailoger.info(digest)
                    step = 3
                except SMTPException as err:
                    if isinstance(err, SMTPAuthenticationError):
                        spiderloger.info(err)
                        break
                    step += 1
                    spiderloger.warning(err, exc_info=True)
                    # debug
                    file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mailerr.log')
                    with open(file, 'a') as f:
                        f.write(digest)
                    time.sleep(1)  # wait and try send mail again
        else:
            # no unread documents
            pass
    except Exception as e:
        spiderloger.exception(e)
