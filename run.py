#!/usr/bin/env python
# coding: utf-8
import os
import time
from oa import JZWJW_NEW, HBCDC, HBWJW, OAini
from oa.exceptions import LoginFailError
from oa.logger import spiderloger, mailoger
from oa.notification import get_mail_digest
from oa.network import check_hbwjw_vpn
from requests.exceptions import ReadTimeout, ConnectionError
from smtplib import SMTPException


def main(ini):
    """
    catch ReadTimeout error for website is down
    """
    if ini.has_option('jzwjw', 'user'):
        try:
            u, p = ini.get('jzwjw', 'user'), ini.get('jzwjw', 'passwd')
            jzwjw = JZWJW_NEW(u, p)
            jzwjw.do()
        except (ReadTimeout, ConnectionError) as e:
            spiderloger.error(e, exc_info=True)
        except LoginFailError:
            pass
    if ini.has_option('hbcdc', 'user'):
        try:
            u, p = ini.get('hbcdc', 'user'), ini.get('hbcdc', 'passwd')
            hbcdc = HBCDC(u, p)
            hbcdc.do()
        except (ReadTimeout, ConnectionError) as e:
            spiderloger.error(e, exc_info=True)
        except LoginFailError:
            pass
    if ini.has_option('hbwjw', 'user'):
        if check_hbwjw_vpn():
            spiderloger.info(u"VPN 已经连接.")
            try:
                u, p = ini.get('hbwjw', 'user'), ini.get('hbwjw', 'passwd')
                hbwjw = HBWJW(u, p)
                hbwjw.do()
            except (ReadTimeout, ConnectionError) as e:
                spiderloger.error(e, exc_info=True)
            except LoginFailError:
                pass
        else:
            spiderloger.warning(u"VPN disconnect. HBWJW can't access.")
    digest = get_mail_digest()
    return digest


if __name__ == '__main__':
    try:
        digest = main(OAini)
        if digest:
            step = 0
            while step < 3:
                try:
                    spiderloger.debug(u'...通知中...%s...' % (step + 1))
                    mailoger.info(digest)
                    step = 3
                except SMTPException as smtperr:
                    step += 1
                    spiderloger.WARNING(smtperr, exc_info=True)
                    # debug
                    file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mailerr.log')
                    with open(file, 'a') as f:
                        f.write(digest)
                    time.sleep(1)  # wait and try send mail again
        else:
            # no unreader documents
            pass
    except Exception as e:
        spiderloger.exception(e)
