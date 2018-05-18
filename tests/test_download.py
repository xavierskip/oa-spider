#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 16/8/15 13:21
# @Author  : xavier
from oa import *
from run import check_vpn, mail_content, start_config, send_email
from pprint import pprint

INI = start_config()

jzwjw_data = {
    'title': 'test-jzwjw',
    'note': '',
    'files': [
        ('http://219.140.163.109:9090/oa/WriteFile?TBNAME=%27OA_FILELIST%27&fileid=10344&filename=%D0%C2%BD%A8%CE%C4%BC%FE%BC%D0%20(2).zip','t.zip'),
        ('http://219.140.163.109:9090/oa/WriteFile?TBNAME=%27OA_FILELIST%27&fileid=10589&filename=%BE%A3%CE%C0%C9%FA%BC%C6%C9%FA%B7%A2%A1%B22016%A1%B3129%BA%C5%A3%BA.pdf','1.pdf'),
        ('http://219.140.163.109:9090/oa/WriteFile?TBNAME=%27OA_FILELIST%27&fileid=10585&filename=%BE%A3%CE%C0%C9%FA%BC%C6%C9%FA%B7%A2%A1%B22016%A1%B3101%BA%C5%A3%BA.pdfhttp://219.140.163.109:9090/oa/WriteFile?TBNAME=%27OA_FILELIST%27&fileid=10585&filename=%BE%A3%CE%C0%C9%FA%BC%C6%C9%FA%B7%A2%A1%B22016%A1%B3101%BA%C5%A3%BA.pdf','2.pdf')
    ]
}

hbwjw_data = {
    'title': 'test-hbwjw',
    'note': '',
    'files': [
        ('http://192.168.20.190/file/801/65/19637/%E5%85%B3%E4%BA%8E%E5%81%9A%E5%A5%BD%E7%9C%81%E7%BA%A7%E5%8F%91%E8%AF%81%E4%B8%AD%E4%BB%8B%E6%9C%BA%E6%9E%84%E7%99%BB%E5%BD%95%E4%B8%AD%E4%BB%8B%E6%9C%8D%E5%8A%A1%E7%BD%91%E5%AE%8C%E6%88%90%E6%B3%A8%E5%86%8C%E5%B7%A5%E4%BD%9C%E7%9A%84%E9%80%9A%E7%9F%A5.pdf','0.pdf'),
        ('http://192.168.20.190/file/800/383/115154/%E5%85%B3%E4%BA%8E%E4%B8%8B%E5%8F%91%E3%80%8A%E8%A1%80%E5%90%B8%E8%99%AB%E7%97%85%E9%98%B2%E6%B2%BB%E8%A7%84%E8%8C%83%E7%89%87%E3%80%8B%E5%92%8C%E3%80%8A%E8%A1%80%E5%90%B8%E8%99%AB%E7%97%85%E9%98%B2%E6%B2%BB%E5%8A%A8%E7%94%BB%E7%89%87%E7%9A%84%E5%87%BD%E3%80%8B.PDF','1.pdf'),
        ('http://192.168.20.190/file/800/380/114107/14%E3%80%81%E5%85%B3%E4%BA%8E%E8%BD%AC%E5%8F%91%E4%B8%AD%E5%9B%BD%E5%81%A5%E5%BA%B7%E4%BF%83%E8%BF%9B%E4%B8%8E%E6%95%99%E8%82%B2%E5%8D%8F%E4%BC%9A%E3%80%8A%E5%85%B3%E4%BA%8E%E4%B8%BE%E5%8A%9E%E9%A6%96%E6%9C%9F%E5%9F%BA%E5%B1%82%E5%8D%AB%E7%94%9F%E6%9C%BA%E6%9E%84%E5%81%A5%E5%BA%B7%E4%BF%83%E8%BF%9B%E4%B8%8E%E6%95%99%E8%82%B2%E5%9F%B9%E8%AE%AD%E4%BA%A4%E6%B5%81%E7%8F%AD%E7%9A%84%E9%80%9A%E7%9F%A5%E3%80%8B%E7%9A%84%E9%80%9A%E7%9F%A5.pdf','2.pdf'),
    ]
}

hbcdc_data = {
    'title': 'test-hbcdc',
    'note': '',
    'files': [
        ('http://oa.hbcdc.com/OA/Sys/Attachment/Download?id=cbf38a0b-5217-4697-a708-576ee73486fa','1.pdf'),
        ('http://oa.hbcdc.com/OA/Sys/Attachment/Download?id=22f05aeb-084f-4553-a492-ab3503b7ea9f','2.pdf'),
    ]
}

# hbwjw test
if check_vpn():
    logger.info("VPN is ready.")
    hbwjw = HBWJW(INI.get('hbwjw', 'user'), INI.get('hbwjw', 'passwd'))
    # hbwjw.save_doc(hbwjw_data)
    url = hbwjw.card_show('http://192.168.20.190/cards/action.php3?card=801&id=31569&act=%CF%EA%CF%B8')
    data = hbwjw.doc_parser(url)
    hbwjw.save_doc(data)
    data = hbwjw.doc_parser('http://192.168.20.190/cards/action/cardshow.php3?act=%E8%AF%A6%E7%BB%86&card=801&id=23969')
    hbwjw.save_doc(data)
    data = hbwjw.mail_parser('http://192.168.20.190/showxx/showxx.php?id=141214')
    hbwjw.save_doc(data)
else:
    logger.warning("VPN not ready.")

# jzwjw test
jzwjw = JZWJW(INI.get('jzwjw', 'user'), INI.get('jzwjw', 'passwd'))
# jzwjw.save_doc(jzwjw_data)
data = jzwjw.doc_parser('http://219.140.163.109:9090/oa/modules/email/email_receive.action?id=9626&type=0')
jzwjw.save_doc(data)
data = jzwjw.doc_parser('http://219.140.163.109:9090/oa/modules/email/email_receive.action?id=9665&type=0')
jzwjw.save_doc(data)

# hbcdc test
hbcdc = HBCDC(INI.get('hbcdc', 'user'), INI.get('hbcdc', 'passwd'))
# hbcdc.save_doc(hbcdc_data)
data = hbcdc.doc_parser('def70f3c-1dfe-49af-91bc-07f1107b710e')
hbcdc.save_doc(data)
data = hbcdc.doc_parser('2fc5db1d-6d62-49eb-95c3-a662bee0e8ed')
hbcdc.save_doc(data)
data = hbcdc.doc_parser('6fd1a8a6-52ee-415a-b108-6393115e6d68')
hbcdc.save_doc(data)
data = hbcdc.mail_parser('3ca1e4d5-68b9-49c1-8197-6a4e8b279e83')
hbcdc.save_doc(data)

#
# for k,v in FILENAMES.iteritems():
#     pprint(k)
#     pprint(v)
content = mail_content()

# pprint(content)
# maillog.debug(mail_content())
send_email(
    INI.get('mail', 'host'),
    INI.get('mail', 'account'),
    INI.get('mail', 'passwd'),
    INI.get('mail', 'address').split(','),
    INI.get('mail', 'subject'),
    content
)
