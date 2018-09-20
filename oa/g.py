#!/usr/bin/env python
# coding: utf-8
import os
import sys

"""
FILENAMES = {
    'name1': [
        {
            'title': 'title',
            'note': 'note',
            'files': [('url','name'),('url','name'),...],
        },
        {...}
    ],
    'name2': [{...},{...},{...}],
    ...
}
"""

FILENAMES = {}  # all get Files for notification
HERE = os.path.dirname(os.path.abspath(__file__))
fsencoding = sys.getfilesystemencoding()  #  windows xp is mbcs
HERE = HERE.decode(fsencoding)

# print(HERE)

CONFIG = {
    'DEBUG': 0,
    'INI': os.path.join(HERE, os.pardir, 'oa.ini'),
    'INBOX_PATH': os.path.join(HERE, os.pardir, 'inbox'),
    'LOG_FILE': os.path.join(HERE, os.pardir, 'spider.log'),
    # 'MAILFILE': os.path.join(HERE, os.pardir, 'notification.html'),
}
