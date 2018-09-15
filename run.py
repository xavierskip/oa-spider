#!/usr/bin/env python
# coding: utf-8
import os
import time
from oa import JZWJW_NEW, HBCDC, HBWJW, logger, OA_ini, LoginFailError
from oa.notification import send_email, generate_mail_content
from oa.network import check_hbwjw_vpn
from requests.exceptions import ReadTimeout, ConnectionError
from smtplib import SMTPException


def todo(ini):
    """
    catch ReadTimeout error for website is down
    """
    if ini.has_option('jzwjw', 'user'):
        try:
            u, p = ini.get('jzwjw', 'user'), ini.get('jzwjw', 'passwd')
            jzwjw = JZWJW_NEW(u, p)
            jzwjw.do()
        except (ReadTimeout, ConnectionError) as e:
            logger.error(e)
        except LoginFailError:
            pass
    if ini.has_option('hbcdc', 'user'):
        try:
            u, p = ini.get('hbcdc', 'user'), ini.get('hbcdc', 'passwd')
            hbcdc = HBCDC(u, p)
            hbcdc.todo()
        except (ReadTimeout, ConnectionError) as e:
            logger.error(e)
        except LoginFailError:
            pass
    if ini.has_option('hbwjw', 'user'):
        if check_hbwjw_vpn():
            logger.info(u"VPN 已经连接.")
            try:
                u, p = ini.get('hbwjw', 'user'), ini.get('hbwjw', 'passwd')
                hbwjw = HBWJW(u, p)
                hbwjw.todo()
            except (ReadTimeout, ConnectionError) as e:
                logger.error(e)
            except LoginFailError:
                pass
        else:
            logger.info(u"VPN 未连接. HBWJW can't access.")
    notification = generate_mail_content()
    # maillog.debug(notification)  # 保存通知文件以便通过其他程序发送邮件
    return notification


if __name__ == '__main__':
    ini = OA_ini
    try:
        notification = todo(ini)
        if notification:
            step = 0
            while step < 3:
                try:
                    logger.debug(u'...发送邮件:%s...' % (step + 1))
                    send_email(
                        ini.get('mail', 'host'),
                        ini.get('mail', 'account'),
                        ini.get('mail', 'passwd'),
                        ini.get('mail', 'address').split(','),
                        ini.get('mail', 'subject'),
                        notification
                    )
                    step = 3
                except SMTPException as smtperr:
                    step += 1
                    file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mailerr.log')
                    with open(file, 'a') as f:
                        f.write(notification)
                    logger.debug(smtperr)
                    time.sleep(1)
        else:
            pass
    except Exception as e:
        logger.exception(e)
        logger.debug(u'...发生错误!发送邮件中...')
        send_email(
            ini.get('mail', 'host'),
            ini.get('mail', 'account'),
            ini.get('mail', 'passwd'),
            ini.get('mail', 'address').split(','),
            'ERROR:oa-spider',
            str(e)
        )
