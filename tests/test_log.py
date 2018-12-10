#!/usr/bin/env python
# coding: utf-8
import logging
spiderlog = logging.getLogger('oa')
spiderlog.setLevel(logging.DEBUG)
spiderlog.addHandler(logging.FileHandler('test.txt', encoding=None))
spiderlog.addHandler(logging.StreamHandler())
spiderlog.info('aa 中文 vv 混合测试')
spiderlog.info(u'Unicode 测试 ')
