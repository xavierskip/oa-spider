#!/usr/bin/env python
# coding: utf-8
import sys
import unittest
from oa import *
from oa.captcha import THRESHOLD, binarization, img_split
from run import main, start_config

CONFIG['DEBUG'] = 1

INI = start_config()

def test_save_doc():
    '''
    download attachements
    '''
    hbcdc = HBCDC(INI.get('hbcdc', 'user'), INI.get('hbcdc', 'passwd'))
    data = hbcdc.doc_parser('d8b3c8ae-606b-48b4-8097-5899fd6c8aa6')
    hbcdc.save_doc(data)
    jzwjw = JZWJW(INI.get('jzwjw', 'user'), INI.get('jzwjw', 'passwd'))
    urls = [
        'http://219.140.163.109:9090/oa/modules/email/email_receive.action?id=9309&type=0',
        'http://219.140.163.109:9090/oa/modules/email/email_receive.action?id=9306&type=0',
        'http://219.140.163.109:9090/oa/modules/email/email_receive.action?id=9294&type=0'
    ]
    for u in urls:
        r = jzwjw.session.get(u)
        data = jzwjw.doc_parser(r.content.decode('GBK'))
        jzwjw.save_doc(data)

def test_all():
    """
    DEBUG = 1, don't go to the document detail page, just fetch documents page
    """
    main()

def test_auto_login():
    """
    login 100 times, success rate
    """
    y = 0
    n = 0
    for i in range(100):
        jzwjw = JZWJW(INI.get('jzwjw', 'user'), INI.get('jzwjw', 'passwd'))
        if jzwjw.auth:
            y += 1
        else:
            n += 1
            print jzwjw.captcha_code
            jzwjw.captcha_img.show()
            bimg = binarization(jzwjw.captcha_img, 135)
            bimg.show()
            for cimg in img_split(bimg):
                cimg.show()
            print y,',',n
            skip = raw_input('')
    print 'y:n %s:%s' %(y,n)

class TestOA(unittest.TestCase):
    pass

if __name__ == '__main__':
    t = sys.argv[1]
    if t == '-test':
        unittest.main()
    if t == '-download':
        test_save_doc()
    if t == '-debug':
        test_all()
    if t == '-login':
        test_auto_login()