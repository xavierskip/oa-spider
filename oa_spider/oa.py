#!/usr/bin/env python
# coding: utf-8
import requests
import os
import sys
import time
import errno
import re
import base64
import ddddocr
from io import BytesIO
from .g import FILENAMES, CONFIG
from .logger import spiderloger as logger
from pyquery import PyQuery
from lxml import etree
from PIL import Image
from .captcha import hack_captcha
from .exceptions import LoginFailError
from requests.exceptions import ChunkedEncodingError
from .JSEncrypt import hbwjw_public_key, encrpt, public_key_format

TIMEOUT = 3

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
    clean_chars += "\n\r"
    clean_chars += u"\u000A\u000B\u000C\u000D\u0085\u2028\u2029" # http://unicode.org/reports/tr18/tr18-5.1.html
    for c in clean_chars:
        name = name.replace(c, '')
    while True:
        if name.endswith('.'):
            name = name[:-1]
        elif name.startswith('.'):
            name = name[1:]
        else:
            break
    # print("clear?", type(name), name)
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

class TimeOutSessions(requests.Session):
    def __init__(self, timeout) -> None:
        self.timeout = timeout
        super().__init__()

    def request(self, *args, **kwargs):
        kwargs.setdefault('timeout', self.timeout)
        return super(TimeOutSessions, self).request(*args, **kwargs)

class Spider(object):
    NAME = "spider"
    HOST = 'http://x.com'
    def __init__(self, username='', password='', *args, **kwargs):
        self.session = TimeOutSessions(TIMEOUT)
        if kwargs.get('proxies') != None:
            self.session.proxies = kwargs.get('proxies')
        if kwargs.get('verify') != None:
            self.session.verify = kwargs.get('verify')
        if username and password:
            # login is first requests
            ok = self.login(username, password)
            if ok:
                self.auth = True
                logger.info(u'%s登录成功✅', self)
            else:
                self.auth = False
                logger.info(u'%s登录失败⚠️', self)

    def __str__(self):
        return getattr(self, "NAME", None) or type(self).__name__

    def URL(self, path):
        return self.HOST+path

    def login(self, u, p):
        '''
        in this funciton,http request need timeout
        '''
        return True

    def downloadfile_info(self, count):
        if count > 0:
            logger.info(u'%s有%d个新文件!' % (self, count))
        else:
            logger.info(u'%s没有新文件.' % self)

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
        note = data['note']
        if isinstance(note, str):
           note = note.strip()
        if note:
            self.write_note(note, path)
            logger.debug(u'通知: %s' % guess_abstract(note))
        for i, (url, name) in enumerate(data['files'], 1):
            try:
                self.download_file(url, name, path, '(%s/%s)' % (i, len(data['files'])))
            except ChunkedEncodingError as e:
                print("NETWORK ERROR⚠️")
                print(e)

    def download_file(self, url, name, path, flag='', timeout=200):
        output = BytesIO()
        start = time.time()
        r = self.session.get(url, stream=True, timeout=timeout)
        length = int(r.headers.get('content-length', 0))
        save = 0.0
        modulus = 1024 * 100
        speed = 0
        for chunk in r.iter_content(chunk_size = modulus):
            output.write(chunk)
            # progress bar
            save += len(chunk)
            t = time.time() - start
            if t != 0:
                speed = save / t
            if length:  # http header with content-length
                size = sizeof_fmt(length)
                rate = '{}%'.format(int(save / length * 100))
                l = '\r{} {} {} {}/s'.format(flag, rate, size, sizeof_fmt(speed))
                sys.stdout.write(l)
                sys.stdout.flush()
                sys.stdout.write(' '*len(l))
                sys.stdout.flush()
            else:      # # http header without content-length
                l = '\r{} {} {}/s'.format(flag, sizeof_fmt(save), sizeof_fmt(speed))
                sys.stdout.write(l)
                sys.stdout.flush()
                sys.stdout.write(' '*len(l))
                sys.stdout.flush()

        name = clean_filename(name)
        with open(os.path.join(path, name), 'wb') as fd:
            fd.write(output.getvalue())
        sys.stdout.flush()
        d = '\r{} {}|{} {:.1f}s {}'.format(flag, sizeof_fmt(save), sizeof_fmt(length), time.time() - start, r.url)
        logger.info(d)

    @need_auth
    def do(self, unread=True, *args, **kwargs):
        documents = self.todo(unread, *args, **kwargs)
        for doc_data in documents:
            self.save_doc(doc_data)

        self.downloadfile_info(len(documents))  # just show the info 

    # @need_auth
    def todo(self, *args, **kwargs):
        ''' self.do() is already @need_auth
        '''
        pass

class HBCDC_wui(Spider):
    NAME = '湖北省疾控中心'
    SITE = 'http://10.68.0.21'
    LOGIN_FORM      = F"{SITE}/api/hrm/login/getLoginForm"
    WEAVER_FILE     = F"{SITE}/weaver/weaver.file.MakeValidateCode"
    RSA_INFO        = F"{SITE}/rsa/weaver.rsa.GetRsaInfo"
    CHECK_LOGIN     = F"{SITE}/api/hrm/login/checkLogin"
    DOC_LIST        = F"{SITE}/api/doc/more/list"
    TABLE_DATAS     = F"{SITE}/api/ec/dev/table/datas"
    DOC_BASIC_INFO  = F"{SITE}/api/doc/detail/basicInfo"
    DOCACC          = F"{SITE}/api/doc/acc/docAcc"
    DL              = F"{SITE}/weaver/weaver.file.FileDownload?fileid={{}}&download=1"
    MAIL_LIST       = F"{SITE}/api/email/list/allList"
    MAIL_VIEW       = F"{SITE}/api/email/view/mailView"
    MAILCONTENTVIEW = F"{SITE}/api/email/view/mailContentView"
    READLOG         = F"{SITE}/api/doc/read/addReadLog"
    MSGREAD         = F"{SITE}/api/msgcenter/homepage/setMsgRead"
    DOCINDEX        = F"{SITE}/spa/document/index.jsp"

    def pretty_match(self, code):
        d = {
            'O': '0',
            'o': '0',
            'I': '1',
            'i': '1',
            'l': '1',
            'b': '0'
        }
        for k in d:
            code = code.replace(k, d[k])
        return code
    
    def validate_code(self, code):
        '''验证码只由4个数字字符组成
        '''
        # 将容易识别错误的字母替换成数字
        code = self.pretty_match(code)
        # 去掉识别成字母的部分
        r = re.findall("\d", code)
        code = ''.join(r)
        # 验证码只由四个数字组成
        if len(code) != 4:
            return False, code
        else:
            return True, code

    def cc(self, func, c=1, result=None):
        ''' 不断尝试以确保得到符合的验证码，间隔时间不断增加。
        '''
        if c == 0:
            return result
        key, code = func()
        ok, code = self.validate_code(code)
        if ok:
            return self.cc(func, 0, (key, code))
        else:
            print('{} code:{}'.format(c, code))
            c += 1
            time.sleep(c)
            return self.cc(func, c)
    
    def get_code(self):
        # get validate code key
        r = self.session.post(self.LOGIN_FORM)
        try:
            validateCodeKey = r.json()['loginSetting']['validateCodeKey']
        except KeyError:
            # some site no need validateCodeKey
            return ('no validateCodeKey', '0123')
        # print(validateCodeKey)
        # get weaver file
        payload = {'validateCodeKey': validateCodeKey}
        r =  self.session.get(self.WEAVER_FILE, params=payload)        
        ocr = ddddocr.DdddOcr(show_ad=False, beta=True)
        code = ocr.classification(r.content)
        # print(validateCodeKey, code)
        
        # write tmp img file
        # temp_dir = os.environ['TEMP']
        # file_name = "{}.jpg".format(code)
        # file_path = os.path.join(temp_dir, "spider_tmp",file_name)
        # with open(file_path, 'wb') as fd:
        #     for chunk in r.iter_content(chunk_size=512):
        #         fd.write(chunk)
        
        return (validateCodeKey, code)   

    def login(self, username, password):
        '''
        todo: 验证码只由数字组成
        '''
        validateCodeKey, code = self.cc(self.get_code)
        # GET rsa info
        now_ts = int(time.time_ns() / 1000000)
        payload = {'ts': now_ts}
        r = self.session.get(self.RSA_INFO, params=payload, timeout=TIMEOUT)
        r_json = r.json()
        ras_code = r_json['rsa_code']
        rsa_flag = r_json['rsa_flag']
        rsa_pub  = public_key_format(r_json['rsa_pub'])
        # login
        r = self.session.post(self.CHECK_LOGIN, data={
            'loginid': encrpt(username+ras_code, rsa_pub)+rsa_flag,
            'userpassword': encrpt(password+ras_code, rsa_pub)+rsa_flag,
            'validatecode': code,
            'validateCodeKey': validateCodeKey,
            'logintype': 1,
            'islanguid': 7,
            'isie': 'false'
        }, timeout=TIMEOUT)
        loginstatus = r.json()['loginstatus']
        if loginstatus == 'true':
            return True
        else:
            # print(r.json()) # debug
            return False
    
    def get_documents(self):
        r = self.session.post(self.DOC_LIST, data={
            'elementmore': '{"tabtitle":"我的文件","orderby":["3","1","2"],"docCatalogIds":["98"],"order":["2","2","2"]}',
            'isNew': 0
        })
        datakey = r.json()['sessionkey']
        r = self.session.post(self.TABLE_DATAS, data={
            'dataKey': datakey,
            'current': 1,
            'sortParams': []
        })
        docs = r.json()['datas']
        return docs
    
    def get_unread_docs(self, data):
        s = data['idspan']
        r = re.search("src='\/images", s)
        return bool(r)
    
    def get_document_files(self, doc):
        docid = doc['id']
        # get doc tile
        payload = {'docid': docid}
        r = self.session.get(self.DOC_BASIC_INFO, params=payload)
        title = r.json()['data']['docSubject']
        # get doc files
        r = self.session.get(self.DOCACC, params=payload)
        # print(r.json())
        datakey = r.json()['sessionkey']
        r = self.session.post(self.TABLE_DATAS, data={
            'dataKey': datakey,
            'current': 1,
            'sortParams': []
        })
        files = r.json()['datas']
        # print(len(files),'file')
        files = [(self.DL.format(f['imagefileid']), f['imagefilename']) for f in files]
        # read already
        self.session.get(self.READLOG, params=payload)
        # get document note
        r = self.session.get(self.DOCINDEX, params={
            'id': docid,
            'router': 1,
        })
        note = PyQuery(r.text)('#weaDocDetailHtmlContent')
        # data
        data = {
            'title': title,
            'note': note.html(),
            'files': files
        }
        return data
    
    def get_unread_mails(self, datas):
        s = datas.get('flagSpan').get('labelId')
        if s == "未读":
            return True
        else:
            return False

    def get_mails(self):
        payload = {'folderid': 0, 'current':1}
        r = self.session.get(self.MAIL_LIST, params=payload)
        datas =  r.json().get('tableBean').get('datas')
        return datas
    
    def get_mail_files(self, mail):
        mailid = mail['id']
        payload = {'mailId': mailid}
        r = self.session.get(self.MAIL_VIEW, params=payload)
        viewbean = r.json().get('viewBean')
        title = viewbean.get('subjectText')
        fileinfos = viewbean.get('fileInfos')
        files = [('{}{}'.format(self.SITE,f['filelink']),f['filename']) for f in fileinfos['fileList']]
        # mail content
        r = self.session.get(self.MAILCONTENTVIEW, params=payload)
        mailcontent = r.json()['mailContent']
        note = base64.b64decode(mailcontent).decode('utf-8')
        data = {
            'title': title,
            'note': note,
            'files': files
        }
        return data

    def clear_unread(self):
        # 文件
        self.session.get(self.MSGREAD, params={'id':16})
        # 邮件
        self.session.get(self.MSGREAD, params={'id':22})


    def todo(self, unread=True, *args, **kwargs):
        documents = []

        docs = self.get_documents()
        if unread:
            docs = filter(self.get_unread_docs, docs)        
        documents = [self.get_document_files(d) for d in docs]

        mails = self.get_mails()
        if unread:
            mails = filter(self.get_unread_mails, mails)
        mail_files = [self.get_mail_files(m) for m in mails]

        # 消除未读提醒
        if unread:
            self.clear_unread()

        documents.extend(mail_files)
        limit = kwargs.get('limit')
        if limit:
            return documents[:limit]
        else:
            return documents

class JZWJW_wui(HBCDC_wui):
    NAME = '荆州市卫生健康委'
    SITE = 'http://61.136.221.87:8088'
    HOST = SITE
    
    LOGIN_FORM      = F"{SITE}/api/hrm/login/getLoginForm"
    WEAVER_FILE     = F"{SITE}/weaver/weaver.file.MakeValidateCode"
    RSA_INFO        = F"{SITE}/rsa/weaver.rsa.GetRsaInfo"
    CHECK_LOGIN     = F"{SITE}/api/hrm/login/checkLogin"
    DOC_WORKFLOW    = F"{SITE}/api/portal/element/workflow"
    LOAD_FORM       = F"{SITE}/api/workflow/reqform/loadForm"
    UPDATE_INFO     = F"{SITE}/api/workflow/reqform/updateReqInfo"

    def get_documents(self):
        # 待办文件
        r = self.session.post(self.DOC_WORKFLOW, data={
            'eid': 12,
            'hpid': 1,
            'subCompanyId': 1,
            'styleid': 1390381555293,
            'ebaseid': 8
        })
        data = r.json()['data']['data']
        return data
    
    def get_unread_docs(self, data):
        return bool(data['requestname']['img'])
    
    def get_document_files(self, doc):
        requestid = doc['requestname']['requestid']
        r = self.session.post(self.LOAD_FORM, data={
            'requestid': requestid
        })
        j = r.json()
        maindata = j['maindata']
        if j['params']['workflowname'] == '文件报送':
            title = maindata['field6756']
            note = maindata['field6759']
            filedatas = maindata['field6760']['specialobj']['filedatas']
            files = [(self.URL(f['loadlink']), f['filename']) for f in filedatas]
        elif j['params']['workflowname'] == '文件传阅':
            title = maindata['field6731']
            note = maindata['field6735']
            filedatas = maindata['field6734']['specialobj']['filedatas']
            files = [(self.URL(f['loadlink']), f['filename']) for f in filedatas]
        # set Reading Status
        r = self.session.post(self.UPDATE_INFO, data={
            'requestid': requestid
        })
        data = {
            'title': title['value'],
            'note': note['value'],
            'files': files
        }
        return data

    def get_mails(self):
        return []

    def get_unread_mails(self, data):
        return False
    
    def get_mail_files(self, mail):
        return []
    
    def clear_unread(self):
        pass

# ABANDON
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
        try:
            (topic, date, sender, addr, att, content), rest = tds[:6], tds[6:]
        except ValueError as e:
            logger.error(e, type(tds), len(tds), tds.text)
        
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

    def todo(self, unread=True, *args, **kwargs):
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

    # def __todo(self):  
    #     todo = self.todo_query()
    #     todo_page = PyQuery(todo.text)
    #     i = 0  # when for loop is empty for the logger.info()
    #     for i, ele in enumerate(todo_page('a').items(), 1):
    #         if CONFIG['DEBUG']:
    #             print(ele.text())
    #         else:
    #             doc_id = ele.attr.onclick.split('\'')[1]
    #             data = self.doc_parser(doc_id)
    #             self.save_doc(data)

    #     self.newdoc_logit(i)


class HBWJW(Spider):
    NAME = '湖北省卫健委'
    SITE = 'https://192.168.20.190'
    LOGIN_URL = F'{SITE}/logined.php3'
    TOKEN_PAGE = F'{SITE}/getToken.php'
    MAIL_PAGE = F'{SITE}/showxx/xxmanage.php'
    NEW_DOCS  = F'{SITE}/cards/getzmmk.php'

    def login(self, username, password):
        r = self.session.post(self.TOKEN_PAGE, timeout=TIMEOUT)
        token = r.json()["token"]
        mima = encrpt(password, hbwjw_public_key)
        payload = {
            'token': token,
            'xingming': username,
            'mima': mima,
            'pwd':  mima,
            'ip': '42.19.253.10'
        }
        r = self.session.post(self.LOGIN_URL, data=payload, allow_redirects=False, timeout=TIMEOUT)
        if r.status_code == 302 and r.headers['location'] == 'index.php3?url=&menuid=':
            return True
        else:
            return False

    def get_mail_page(self, page):
        payload = {'page': page}
        return self.session.get(self.MAIL_PAGE, params=payload)

    def to_url(self, url):
        r = self.session.get(url)
        # $.get("/showxx/showxx.php?id=352888", function(data){
        location = re.search(r'get\(\"(.+)\"\,', r.content.decode('utf-8')).group(1)
        return self.SITE + location

    def card_show(self, url):
        """ js window.location """
        params = url_params(url)
        return f"{self.SITE}/cards/action/cardshow.php3?act=详细&card={params['card']}&id={params['id']}"

    def get_new_docs(self):
        return self.session.get(self.NEW_DOCS, params={'zhi': 59})

    def get_new_mails(self):
        return self.session.get(self.NEW_DOCS, params={'zhi': 62})

    def fetch_todo_mail_urls(self, page):
        r = self.get_mail_page(page)
        page = PyQuery(r.content.decode('utf-8'))
        urls = []
        for e in page('tr > td:nth-child(2) > a > b').items():
            e = e.parent()
            title, path = e.attr['title'], e.attr['href']
            urls.append(self.to_url(path))
        return urls

    def fetch_mail_urls(self, page):
        r = self.get_mail_page(page)
        page = PyQuery(r.content.decode('utf-8'))
        urls = []
        for e in page('tr > td:nth-child(2) > a').items():
            title, path = e.attr['title'], e.attr['href']
            urls.append((self.to_url(self.SITE + path), title))
        return urls

    def doc_parser(self, url):
        r = self.session.get(url)
        pq = PyQuery(r.content.decode('utf-8'))
        td = pq('#oDetailTable_Body > tr:nth-child(3) > td > table > tbody > tr:nth-child(1) > td')
        title = td.contents()[1]  # <td><B><FONT>xxx</FONT>：</B>xxx</td>
        files = []
        for a in pq('center  a').items():
            if a.attr['href'].startswith('/word/view'):
                continue  # 跳过预览 word 文件的链接
            url = self.SITE + a.attr['href']
            name = url[url.rfind('/') + 1:]
            files.append((url, name))
        return {
            'title': title,
            'note': '',
            'files': files,
        }

    def mail_parser(self, url):
        r = self.session.get(url)
        pq = PyQuery(r.content.decode('utf-8'))
        table = pq('div > table')
        title = table(
            'tr:nth-child(2) > td > div > table > tr:nth-child(1) > td > table > tr:nth-child(2) > td > div > table  > tr:nth-child(4) > td:nth-child(2)')
        note = table(
            'tr:nth-child(2) > td > div > table > tr:nth-child(1) > td > table > tr:nth-child(2) > td > div > table > tr:nth-child(7) > td')
        files = table(
            'tr:nth-child(2) > td > div > table  > tr:nth-child(1) > td > div > table > tr:nth-child(2) > td a')
        return {
            'title': title.text(),
            'note': note.html(),  # + '<p><a href="{0}">{0}</a></p>'.format(url) if note.text() else '',
            'files': [(self.SITE + a.attr.href, a.text()) for a in filter(
                    lambda a:not a.attr.href.startswith('/word/view'), files.items()  # 过滤查看链接
                )
            ],
        }

    def todo(self, unread=True):
        documents = []
        tmp_path = []
        url_list = []
        news_pq = PyQuery(self.get_new_docs().content.decode('utf-8'))
        mails_pq = PyQuery(self.get_new_mails().content.decode('utf-8'))

        for ele in news_pq('.ul1 li').items():
            # name = e.children().attr['title']
            # url_list.append(self.card_show(self.SITE + ele('a').attr['href']))
            tmp_path.append(ele('a').attr['href'])

        for ele in mails_pq('.ul1 li').items():
            # name = e.children().attr['title']
            # url_list.append(self.to_url(self.SITE + ele('a').attr['href']))
            tmp_path.append(ele('a').attr['href'])

        for p in tmp_path:
            if p.find("action.php3?") != -1:
                url_list.append(self.card_show(self.SITE + p))
                continue
            elif p.find("tourl.php?") != -1:
                url_list.append(self.to_url(self.SITE + p))
            else:
                logger.error('%s unknow path: %s' %(self, p))
        
        # print(url_list)

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
    # def test(self, page=1):
    #     links = self.fetch_mail_urls(page)
    #     for url, name in links:
    #         if CONFIG['DEBUG']:
    #             print(url, name)
    #         else:
    #             data = self.mail_parser(url)
    #             self.save_doc(data)

    #     self.newdoc_logit(len(links))

    # @need_auth
    # def __todo(self, page=1): 
    #     links = self.fetch_todo_mail_urls(page)
    #     for url, name in links:
    #         if CONFIG['DEBUG']:
    #             print(url, name)
    #         else:
    #             data = self.mail_parser(url)
    #             self.save_doc(data)

    #     self.newdoc_logit(len(links))


# ABANDON!!! history oa
class JZWJW(Spider):
    NAME = u'荆州市卫计委'
    ORIGIN = 'http://219.140.163.109:9090'
    LOGIN_URL = '%s/oa/function/org/login.action' % ORIGIN

    def get_captcha_img(self):
        url = '%s/oa/login/image.jsp' % self.ORIGIN
        r = self.session.get(url, timeout=TIMEOUT)
        # with open('captcha.jpg', 'wb') as jpg:
        #     jpg.write(r.content)
        return Image.open(BytesIO(r.content))

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

# ABANDON
class JZWJW_ZW(Spider):
    NAME = u'荆州市卫健委（专）'
    ORIGIN = 'http://172.23.254.162:8030/yzoa/'
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

    def todo(self, unread=True, range=None):
        documents = []
        docs = self.get_documents_json()['rows']
        if unread:  # filter received documents
            f = lambda x: x['isReceived'] != '2'
            docs = filter(f, docs)
        if range != None:
            if type(range) == int:
                docs = [docs[range]]
            if type(range) == list or type(range) == tuple:
                s,e = range
                docs = docs[s:e]
        for doc in docs:
            doc_dict = doc['sendDocument']
            doc_data = {
                'title': doc_dict['title'],
                'note': doc['remarks'],  # unknow
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
