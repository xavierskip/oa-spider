#!/usr/bin/env python
# coding: utf-8
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from g import FILENAMES
import smtplib
import subprocess

'''
send_email(
    'smtp.163.com',
    'from@163.com',
    'passwd',
    ['to@163.com','to@qq.com'],
    '全部一起发送',
    content,
)

'''

def get_mail_digest():
    html = ''
    for name, dataset in FILENAMES.items():
        li = ''
        for d in dataset:
            ul = '<ul>%s</ul>' % ''.join(['<li>%s</li>' % n for u, n in d['files']])
            p = '<p>%s</p>' % d['note'] if d['note'] else ''
            li += '<li><b>%s</b>%s%s</li>' % (d['title'], p, ul)
        html += '<h2>[%s]</h2><ol>%s</ol>' % (name, li)  # file titles is unicode
    return html


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


def send_email(smtp_host, from_account, from_passwd, to_accounts, subject, content, mimetype = "html", debuglevel = 0):
    email_client = smtplib.SMTP_SSL(smtp_host)
    email_client.set_debuglevel(debuglevel)
    email_client.login(from_account, from_passwd)
    msg = MIMEText(content, mimetype, 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = _format_addr('公文爬虫 <%s>' % from_account)
    msg['To'] = ','.join(to_accounts)
    email_client.sendmail(from_account, to_accounts, msg.as_string())
    email_client.quit()


def send_mutt(subject, to_addr, file_path):
    args = ['/usr/bin/mutt', '-s', subject,  to_addr, '<', file_path]
    subprocess.call(args)