#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 16/8/31 23:21
# @Author  : xavier
from oa import clean_filename
import unittest


class Test(unittest.TestCase):
    def test_clean_filename(self):
        assert clean_filename('e\/:*?"<>|e') == 'ee'
        assert clean_filename('e\\\/:*?"<>|e') == 'ee'
        assert clean_filename('e\\/:*?"<>|e') == 'ee'


if __name__ == '__main__':
    unittest.main()
