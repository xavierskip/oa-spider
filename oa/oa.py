#!/usr/bin/env python
# coding: utf-8
import requests
import os
import sys
import time
import errno
import re
import StringIO
from g import FILENAMES, CONFIG
from logger import spiderloger as logger
from pyquery import PyQuery
from lxml import etree
from PIL import Image
from captcha import hack_captcha
from exceptions import LoginFailError

TIMEOUT = 10

def guess_abstract(string, len=36):
    # gs = re.finditer(u'[\u4E00-\u9FA5]', string)
    # chars = []
    # for g in gs:
    #     chars.append(g.group())
    #     if len(chars) >= 12:
    #         break
    # return ''.join(chars)
    html = PyQuery(string)
    content = html.text()[:len]
    return content + '[...]'

def clean_filename(name):
    """ windows file name can't include those chars
    http://stackoverflow.com/questions/1033424/how-to-remove-bad-path-characters-in-python
    """
    clean_chars = r'<>:"/\|?*'
    for c in clean_chars:
        name = name.replace(c, '')
    while True:
        if name.endswith('.'):
            name = name[:-1]
        elif name.startswith('.'):
            name = name[1:]
        else:
            break
    return name


def mkdir_p(folder):
    abs_path = os.path.join(CONFIG['INBOX_PATH'], folder)
    try:
        os.makedirs(abs_path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(abs_path):
            r = re.findall('\((\d+)\)$', folder)
            if r:
                n = int(r[0]) + 1
                folder = re.sub('\((\d+)\)$', '(%d)' % n, folder)
            else:
                folder += '(1)'
            return mkdir_p(folder)
        else:
            raise exc
    return abs_path


def url_params(url):
    params = {}
    for parameter in url[url.rfind('?') + 1:].split('&'):
        k, v = parameter.split('=')
        params[k] = v
    return params


def sizeof_fmt(num, suffix='B', modulus=1024):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < float(modulus):
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= float(modulus)
    return "%.1f%s%s" % (num, 'Y', suffix)


def need_auth(func):  # oa system should login to do something
    def wrapper(self, *args, **kw):
        if self.auth:
            return func(self, *args, **kw)
        else:
            raise LoginFailError

    return wrapper


class Spider(object):
    NAME = "spider"
    def __init__(self, username='', password=''):
        self.session = requests.Session()
        if username and password:
            if self.login(username, password):
                self.auth = True
                logger.info(u'%s登录成功', self)
            else:
                self.auth = False
                logger.info(u'%s登录失败', self)

    def __unicode__(self):
        return getattr(self, "NAME", None) or type(self).__name__

    def login(self, u, p):
        '''
        in this funciton,http request need timeout
        '''
        return True

    def downloadfile_info(self, count):
        if count > 0:
            logger.info(u'%s有%d个新文件' % (self, count))
        else:
            logger.info(u'%s没有新文件' % self)

    def write_note(self, content, path):
        html = """<!DOCTYPE html><html><head><meta charset="utf-8"></head>
        <body style="font-size:3em;">%s</body></html>""" % content
        filename = u'通知.html'
        with open(os.path.join(path, filename), 'wb') as f:
            f.write(content.encode("UTF-8"))

    def save_doc(self, data):
        """
        mkdir dir to save the document attachements
        data = {
            'title': 'title',
            'note': 'note',
            'files': [('url', 'name'),...]
        }
        """
        FILENAMES.setdefault(self.NAME, []).append(data)
        title = data['title'].strip()
        path = mkdir_p(clean_filename(title))
        logger.info(u' → {}'.format(title))
        if data['note']:
            self.write_note(data['note'], path)
            logger.debug(u'通知: %s' % guess_abstract(data['note']))
        for i, (url, name) in enumerate(data['files'], 1):
            self.download_file(url, name, path, '(%s/%s)' % (i, len(data['files'])))

    def download_file(self, url, name, path, flag='', timeout=200):
        output = StringIO.StringIO()
        start = time.time()
        r = self.session.get(url, stream=True, timeout=timeout)
        length = int(r.headers.get('content-length', 0))
        save = 0.0
        modulus = 1024
        speed = 0
        for chunk in r.iter_content(modulus * 100):
            output.write(chunk)
            # progress bar
            save += len(chunk)
            t = time.time() - start
            if t != 0:
                speed = save / t
            if length:
                size = sizeof_fmt(length)
                rate = '{}%'.format(int(save / length * 100))
                sys.stdout.flush()
                sys.stdout.write('\r{} {} {} {}/s'.format(flag, rate, size, sizeof_fmt(speed)))
            else:
                sys.stdout.flush()
                sys.stdout.write('\r{} {} {}/s'.format(flag, sizeof_fmt(save), sizeof_fmt(speed)))

        name = clean_filename(name)
        with open(os.path.join(path, name), 'wb') as fd:
            fd.write(output.getvalue())
        sys.stdout.flush()
        d = '\r{} {}|{} {:.1f}s {}'.format(flag, sizeof_fmt(save), sizeof_fmt(length), time.time() - start, r.url)
        logger.info(d)

    @need_auth
    def do(self, unread=1, *args, **kwargs):
        documents = self.todo(unread, *args, **kwargs)
        for doc_data in documents:
            self.save_doc(doc_data)

        self.downloadfile_info(len(documents))  # just show the info 


class HBCDC(Spider):
    NAME = u'湖北省疾控中心'
    UID = 'f056de79-8871-4a62-930c-95ee6c00ca93'  # todo:the UID is what?
    LOGIN_URL = 'http://oa.hbcdc.com/Platform/Login'
    FRec_URL = 'http://oa.hbcdc.com/Platform/Od/FileReceiver/Read'  # POST Form Data:id
    FProc_URL = 'http://oa.hbcdc.com/Platform/Od/FileProcess/Detail'  # POST Form Data:id
    FInfo_URL = 'http://oa.hbcdc.com/Platform/Od/FileInfomation/Read'  # POST Form Data:Id
    DOWNLOAD_URL = 'http://oa.hbcdc.com/OA/Sys/Attachment/Download'  # GET parameter:id
    MailBoxRead_URL = 'http://oa.hbcdc.com/Platform/Msg/MailBox/Read'  # POST
    MailDetail_URL = 'http://oa.hbcdc.com/Platform/Msg/Mail/Detail'  # GET parameter:mailBoxId

    def login(self, username, password):
        payload = {
            'username': username,
            'password': password,
        }
        r = self.session.post(self.LOGIN_URL, data=payload, timeout=TIMEOUT)
        if r.json()['success']:
            return True
        else:
            return False

    def doc_query(self, sort_s='CreatedTime', dir_s='desc', page=1, start=0, limit=25):
        """ POST return json
        """
        query_url = 'http://oa.hbcdc.com/OA/Flow/Index/Query'
        payload = {
            'Q_Userid_S_EQ': self.UID,
            'sort': sort_s,
            'dir': dir_s,
            'Q_Title_S_LK': '',
            'Q_Type_S_EQ': '',
            'Q_ReadStatus_I_EQ': '',
            'Q_CreatedTime_D_GT': '',
            'Q_CreatedTime_D_LT': '',
            'page': page,
            'start': start,
            'limit': limit,
        }
        r = self.session.post(query_url, data=payload)
        return r.json()

    def doc_parser(self, doc_id):
        read = self.session.post(self.FRec_URL, data={'id': doc_id}).json()['data']
        detail = self.session.post(self.FProc_URL, data={'id': read['FileProcessId']})
        doc_info = self.session.post(self.FInfo_URL, data={'id': read['FileInfomationId']})
        info = doc_info.json()['data']
        content = PyQuery(detail.text)('.table-info tr td')
        note = ''
        if content.text():
            # detail_url = '%s?id=%s' % (self.FProc_URL, read['FileProcessId'])
            note = content.html()  # + '<p><a href="{0}">{0}</a></p>'.format(detail_url)
        fileids = info['FileIds'].split(',') if info['FileIds'] else []
        filenames = info['FileNames'].split(',') if info['FileNames'] else []
        files = [('%s?id=%s' % (self.DOWNLOAD_URL, fileid), name) for fileid, name in
                 zip(fileids, filenames)]
        return {
            'title': read['Title'],
            'note': note,
            'files': files,
        }

    def mail_parser(self, mail_box_id):
        mail_detail = self.session.get(self.MailDetail_URL, params={'mailBoxId': mail_box_id})
        mail_content = PyQuery(mail_detail.text)
        tds = mail_content('tr td')
        # if len(tds) != 6:
        #     logger.error('mailBoxId:%s\n%s\n' %(mail_box_id, mail_detail.text))
        #     raise ValueError
        (topic, date, sender, addr, att, content), rest = tds[:6], tds[6:]
        if rest:
            att = content 
            content = rest[0]
            logger.info('mailBoxId:%s\n%s' %(mail_box_id, mail_detail.text))
        ids_names = [(re.search('Id:\'(.+)\'', d.find('a').get('onclick')).group(1), d.find('a').text) for d in att]
        note = content.text if type(content) == etree._Element else content.text_content()
        return {
            'title': topic.text,
            'note': note.strip(),
            'files': [('%s?id=%s' % (self.DOWNLOAD_URL, i), name) for i, name in ids_names],
        }

    def official_parser(self, Id):
        url = 'http://oa.hbcdc.com/FlowPortal/Workspace/HBCDC/OD/HBSWSheet.aspx'
        payload = {
            'Mode': 'Print',
            'WorkItemID': Id
        }
        headers = {'Accept-Language': 'zh-CN'}  #I don't know why should add this request header
        r = self.session.get(url, params=payload, headers=headers)
        official_content = PyQuery(r.text)
        ele_title = official_content('#ctrlTitle')
        # get Attachment file
        att_url = 'http://oa.hbcdc.com/Platform/Sys/Attachment/Read'
        att_id = official_content('#ctrlContentFile').text()
        att_r = self.session.post(att_url, data={'id': att_id})
        filename = att_r.json()['data']['FileName']
        fileURL = '%s?id=%s' % (self.DOWNLOAD_URL, att_id)
        # read confirm
        self.official_read_confirm(Id)
        return {
            'title': u'【公文处理】'+ele_title.text(),
            'note': r.text,
            'files': [(fileURL, filename)],  # something trouble
        }

    def official_read_confirm(self, Id):
        url = 'http://oa.hbcdc.com/FlowPortal/WorkItemDetail.aspx'
        payload = {
            'WorkItemID': Id
        }
        headers = {'Accept-Language': 'zh-CN'}  #Special header
        return self.session.get(url, params=payload, headers=headers, allow_redirects=False)

    def todo(self, unread=1, *args, **kwargs):
        documents = []
        docs = self.doc_query(**kwargs)['data']
        if unread:  # filter received documents
            f = lambda x: x['ReadStatus'] == 0
            docs = filter(f, docs)
        for doc in docs:
            if doc['Type'] == u'文件':
                doc_data = self.doc_parser(doc['Id'])
                documents.append(doc_data)
            elif doc['Type'] == u'邮件':
                doc_data = self.mail_parser(doc['Id'])
                documents.append(doc_data)
            elif doc['Type'] == u'公文':
                doc_data = self.official_parser(doc['Id'])
                documents.append(doc_data)
            else:
                logger.warning(u'miss type %s\n%s' %(doc['Type'], doc))
        return documents

    # ABANDON!
    def todo_query(self):
        """ POST return HTML
        """
        todo_url = 'http://oa.hbcdc.com/OA/Flow/Index/Todo'
        payload = {
            'Q_Userid_S_EQ': self.UID,
            'Q_ReadStatus_I_EQ': 0,
            'Q_Type_S_IN': '公文,文件,内部请示报告',
            'start': 0,
            'limit': 100,
            'sort': 'CreatedTime',
            'dir': 'desc',
        }
        return self.session.post(todo_url, data=payload)

    def __todo(self):  
        todo = self.todo_query()
        todo_page = PyQuery(todo.text)
        i = 0  # when for loop is empty for the logger.info()
        for i, ele in enumerate(todo_page('a').items(), 1):
            if CONFIG['DEBUG']:
                print(ele.text())
            else:
                doc_id = ele.attr.onclick.split('\'')[1]
                data = self.doc_parser(doc_id)
                self.save_doc(data)

        self.newdoc_logit(i)


class HBWJW(Spider):
    NAME = u'湖北省卫计委'
    ORIGIN = 'http://192.168.20.190'
    LOGIN_URL = 'http://192.168.20.190/logined.php3'

    def login(self, username, password):
        r = self.session.get('http://192.168.20.190/login.php3', timeout=TIMEOUT)
        page = PyQuery(r.content.decode('gbk'))
        token = page('input[type="hidden"]').attr('value')
        payload = {
            'token': token,
            'xingming': username.decode('utf-8').encode('gbk'),
            'mima': password,
        }
        r = self.session.post(self.LOGIN_URL, data=payload, allow_redirects=False, timeout=TIMEOUT)
        if r.status_code == 302 and r.headers['location'] == 'index.php3?url=&menuid=':
            return True
        else:
            return False

    def get_mail_page(self, page):
        url = 'http://192.168.20.190/showxx/xxmanage.php'
        payload = {'page': page}
        return self.session.get(url, params=payload)

    def to_url(self, url):
        r = self.session.get(url)
        # print(url)
        # print(r.content)
        return self.ORIGIN + re.findall('location=\'(.+)\'', r.content)[0]

    def card_show(self, url):
        """ js window.location """
        s = 'http://192.168.20.190/cards/action/cardshow.php3?act=详细&card={0}&id={1}'
        params = url_params(url)
        return s.format(params['card'], params['id'])

    def get_new_docs(self):
        return self.session.get('http://192.168.20.190/cards/getzmmk.php', params={'zhi': 59})

    def get_new_mails(self):
        return self.session.get('http://192.168.20.190/cards/getzmmk.php', params={'zhi': 62})

    def fetch_todo_mail_urls(self, page):
        r = self.get_mail_page(page)
        page = PyQuery(r.content.decode('gbk'))
        urls = []
        for e in page('tr > td:nth-child(2) > a > b').items():
            e = e.parent()
            title, path = e.attr['title'], e.attr['href']
            urls.append(self.to_url(path))
        return urls

    def fetch_mail_urls(self, page):
        r = self.get_mail_page(page)
        page = PyQuery(r.content.decode('gbk'))
        urls = []
        for e in page('tr > td:nth-child(2) > a').items():
            title, path = e.attr['title'], e.attr['href']
            urls.append((self.to_url(self.ORIGIN + path), title))
        return urls

    def doc_parser(self, url):
        r = self.session.get(url)
        pq = PyQuery(r.content.decode('gbk'))
        td = pq('#oDetailTable_Body > tr:nth-child(3) > td > table > tbody > tr:nth-child(1) > td')
        title = td.contents()[1]  # <td><B><FONT>xxx</FONT>：</B>xxx</td>
        files = []
        for a in pq('center  a').items():
            if a.attr['href'].startswith('/word/view'):
                continue  # 跳过预览 word 文件的链接
            url = self.ORIGIN + a.attr['href']
            name = url[url.rfind('/') + 1:]
            files.append((url, name))
        return {
            'title': title,
            'note': '',
            'files': files,
        }

    def mail_parser(self, url):
        r = self.session.get(url)
        pq = PyQuery(r.content.decode('gbk'))
        table = pq.children('div > table')
        title = table(
            'tr:nth-child(2) > td > div > table > tr:nth-child(1) > td > table > tr:nth-child(2) > td > div > table  > tr:nth-child(4) > td:nth-child(2)')
        note = table(
            'tr:nth-child(2) > td > div > table > tr:nth-child(1) > td > table > tr:nth-child(2) > td > div > table > tr:nth-child(7) > td')
        files = table(
            'tr:nth-child(2) > td > div > table  > tr:nth-child(1) > td > div > table > tr:nth-child(2) > td a')
        return {
            'title': title.text(),
            'note': note.html(),  # + '<p><a href="{0}">{0}</a></p>'.format(url) if note.text() else '',
            'files': [(self.ORIGIN + a.attr.href, a.text()) for a in filter(
                    lambda a:not a.attr.href.startswith('/word/view'), files.items()  # 过滤查看链接
                )
            ],
        }

    def todo(self, unread=1):
        documents = []
        url_list = []
        news_pq = PyQuery(self.get_new_docs().content.decode('gbk'))
        mails_pq = PyQuery(self.get_new_mails().content.decode('gbk'))

        for ele in news_pq('.ul1 li').items():
            # name = e.children().attr['title']
            url_list.append(self.card_show(self.ORIGIN + ele('a').attr['href']))

        for ele in mails_pq('.ul1 li').items():
            # name = e.children().attr['title']
            url_list.append(self.to_url(self.ORIGIN + ele('a').attr['href']))

        for url in url_list:
            if url.find('/cards/action/cardshow.php3') != -1:
                doc_data = self.doc_parser(url)
                documents.append(doc_data)
            elif url.find('/showxx/showxx.php') != -1:
                doc_data = self.mail_parser(url)
                documents.append(doc_data)
            else:
                # print('unknow url', url)
                logger.error('%s unknow url: %s' %(self, url))

        return documents

    # ABANDON!
    def test(self, page=1):
        links = self.fetch_mail_urls(page)
        for url, name in links:
            if CONFIG['DEBUG']:
                print(url, name)
            else:
                data = self.mail_parser(url)
                self.save_doc(data)

        self.newdoc_logit(len(links))

    @need_auth
    def __todo(self, page=1): 
        links = self.fetch_todo_mail_urls(page)
        for url, name in links:
            if CONFIG['DEBUG']:
                print(url, name)
            else:
                data = self.mail_parser(url)
                self.save_doc(data)

        self.newdoc_logit(len(links))


''' ABANDON!
class JZWJW(Spider):  # abandoned!
    NAME = u'荆州市卫计委'
    ORIGIN = 'http://219.140.163.109:9090'
    LOGIN_URL = '%s/oa/function/org/login.action' % ORIGIN

    def get_captcha_img(self):
        url = '%s/oa/login/image.jsp' % self.ORIGIN
        r = self.session.get(url, timeout=TIMEOUT)
        # with open('captcha.jpg', 'wb') as jpg:
        #     jpg.write(r.content)
        return Image.open(StringIO.StringIO(r.content))

    def login(self, username, password):
        headerl = '%s/oa/function/org/../../index.jsp' % self.ORIGIN
        self.captcha_img = self.get_captcha_img()
        # captcha_img.show()
        # code = raw_input('code:')
        self.captcha_code = hack_captcha(self.captcha_img)
        payload = {
            'username': username,
            'password': password,
            'input': self.captcha_code,
            'ip': '61.184.206.86'
        }
        r = self.session.post(self.LOGIN_URL, data=payload, allow_redirects=False, timeout=TIMEOUT)
        if r.headers['location'] == headerl:
            return True
        else:
            return False

    def test_login(self):
        index_url = '%s/oa/modules/email/email_list.action?type=3' % self.ORIGIN
        r = self.session.get(index_url)
        with open('list.html', 'w') as html:
            html.write(r.content)
        return r

    def get_mails_page(self, type_id, pagesize=15, rowstart=0):
        """
        type: 0 for all mails, 3 for todo mails
        pagesize: offset
        rowstart: index
        """
        url = '%s/oa/modules/email/email_list.action' % self.ORIGIN
        payload = {
            'type': type_id,
            'pagesize': pagesize,
            'rowstart': rowstart,
        }
        return self.session.get(url, params=payload)

    def page_parser(self, content):
        emailu = '%s/oa/modules/email/' % self.ORIGIN
        pq = PyQuery(content)
        urls = []
        for a in pq('table.coolTable tr td:nth-child(2) a').items():
            url, name = emailu + a.attr['href'], a.text()
            urls.append((url, name))
        return urls

    def doc_parser(self, url):
        r = self.session.get(url)
        pq = PyQuery(r.content.decode('GBK'))
        title = pq('.TableForm tr:first td')[1].text
        file_no = pq('.TableForm tr').eq(2)('td')[3].text
        if file_no:
            title = u'%s：%s' % (file_no, title)
        note = pq('table.TableForm tr').eq(5)('td')
        if note.text():
            note = note.html()
        else:
            note = ''
        iframe = pq('#uploadFile')
        uploadfile_url = '%s%s' % (self.ORIGIN, iframe.attr['src'])
        r = self.session.get(uploadfile_url)
        print(r.status_code, r.url)
        iframe_pq = PyQuery(r.content)
        # ipdb.set_trace()
        files = []
        for a in iframe_pq('form a').items():
            url = self.ORIGIN + a.attr['href']
            t = a.text()
            n = t.rfind('(')
            name = t[:n]
            files.append((url, name))
        return {
            'title': title,
            'note': note,
            'files': files,
        }

    @need_auth
    def todo(self, type_id=3, pagesize=15):
        r = self.get_mails_page(type_id, pagesize)
        links = self.page_parser(r.content.decode('GBK'))
        for url, name in links:
            if CONFIG['DEBUG']:
                print(url, name)
            else:
                data = self.doc_parser(url)
                self.save_doc(data)

        self.newdoc_logit(len(links))

    @need_auth
    def test(self):
        r = self.get_mails_page(3, 100)
        links = self.page_parser(r.content.decode('GBK'))
        for url, name in links:
            if CONFIG['DEBUG']:
                print(name)
            else:
                data = self.doc_parser(url)
                self.save_doc(data)

        self.newdoc_logit(len(links))

    @need_auth
    def test_decorator(self, a='test'):
        print(a, 'Decorator test!!!')
'''

class JZWJW_NEW(Spider):
    NAME = u'荆州市卫计委'
    ORIGIN = 'http://172.23.254.254:8888/yzoa'
    LOGIN_URL = '%s/user/login' % ORIGIN

    def login(self, username, password):
        payload = {
            'userName': username,
            'password': password
        }
        r = self.session.post(self.LOGIN_URL, data=payload, timeout=TIMEOUT)
        rs = r.json()
        return rs['result']

    def get_documents_json(self, page=1, rows=40):
        url = '%s/oa/sendDocumentUser/list' % self.ORIGIN
        payload = {
            'page': page,
            'rows': rows,
            'sourceType': 1
        }
        r = self.session.post(url, data=payload)
        return r.json()

    def read_confirm(self, id):
        url = '%s/oa/sendDocumentUser/view' % self.ORIGIN
        payload = {
            'id': id
        }
        r = self.session.get(url, params=payload)
        return r

    def get_attachment_json(self, documentId):
        url = '%s/oa/document/file/list' % self.ORIGIN
        payload = {
            'documentId': documentId
        }
        r = self.session.get(url, params=payload)
        return r.json()

    def sendDocument_download_URL(self, id):
        return "%s/oa/sendDocument/download/%s" %(self.ORIGIN, id)

    def document_download_URL(self, id):
        return "%s/oa/document/file/download/%s" %(self.ORIGIN, id)

    def todo(self, unread=1):
        documents = []
        docs = self.get_documents_json()['rows']
        if unread:  # filter received documents
            f = lambda x: x['isReceived'] != '2'
            docs = filter(f, docs)
        for doc in docs:
            doc_dict = doc['sendDocument']
            doc_data = {
                'title': doc_dict['title'],
                'note': doc_dict['content'],  # unknow
                'files': [],
            }
            # sendDocument file
            url, name = self.sendDocument_download_URL(doc_dict['id']), doc_dict['docuFileName']
            doc_data['files'].append((url, name))
            # attachment files
            for i in self.get_attachment_json(doc_dict['id']):
                url, name = self.document_download_URL(i['id']), i['fileName']
                doc_data['files'].append((url, name))
            documents.append(doc_data)
            # read confirm
            self.read_confirm(doc['id'])

        return documents
