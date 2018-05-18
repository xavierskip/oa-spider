#!/usr/bin/env python
# coding: utf-8
from captcha import *
from PIL import Image
import unittest

class Test(unittest.TestCase):

    def test_img_compare(self):
        filenames = filter(lambda n: n.endswith('png'), os.listdir('models'))
        paths = map(lambda n: os.path.join('models', '%s' %n), filenames)
        imgs = map(lambda f: Image.open(f), paths)
        for i, imga in enumerate(imgs):
            result = []
            for j, imgb in enumerate(imgs):
                result.append([j, img_compare(imga, imgb)])
            for x,r in sorted(result, key=lambda x: x[1], reverse=True):
                print "%s:%s %s" %(i,x,r)
            print '='*10

    def test_continuous_lines(self):
        # s0 = []
        s1 = [1,0,0,0,0,1,1,1,1,1,1,0]
        s2 = [0,0,0,1,1,1,1,0,0,0,0,1,1,1,1,1,1,0]
        s3 = [0,0,0,1,1,1,1,0,0,0,0,1,1,1,1,1,1,1]
        s4 = [1,1,1,1,0,0,1,0,1,0,1,0,0,0,0,0,0,0]
        s5 = [1,1,1,1,0,0,1,0,1,0,1,0,0,0,1,1,1,1]
        s6 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        s7 = [0,0,0,0,1,1,1,1,0,0,0,0]
        s8 = [0,0,0,0,1,1,0,0,1,0,1,0,1,0,0,0,1,1,1,1,0,0]
        s9 = [0,0,0,0,1,0,0,0]
        # assert continuous_lines(s0) == [], continuous_lines(s0)
        # assert continuous_lines(s0, 1) == [0,0], continuous_lines(s0)
        assert continuous_lines(s1) == [[0,1],[5,11]], continuous_lines(s1)
        assert continuous_lines(s1, 1) == [0,11], continuous_lines(s1)
        assert continuous_lines(s2) == [[3,7],[11,17]], continuous_lines(s2)
        assert continuous_lines(s2, 1) == [3, 17], continuous_lines(s2)
        assert continuous_lines(s3) == [[3,7],[11,18]], continuous_lines(s3)
        assert continuous_lines(s3, 1) == [3,18], continuous_lines(s3)
        assert continuous_lines(s4) == [[0,4],[6,7],[8,9],[10,11]], continuous_lines(s4)
        assert continuous_lines(s4, 1) == [0,11], continuous_lines(s4)
        assert continuous_lines(s5) == [[0,4],[6,7],[8,9],[10,11],[14,18]], continuous_lines(s5)
        assert continuous_lines(s5, 1) == [0,18], continuous_lines(s5)
        assert continuous_lines(s6) == [], continuous_lines(s6)
        assert continuous_lines(s6, 1) == [0,0], continuous_lines(s6)
        assert continuous_lines(s7) == [[4,8]], continuous_lines(s7)
        assert continuous_lines(s7, 1) == [4,8], continuous_lines(s7)
        assert continuous_lines(s8) == [[4,6],[8,9],[10,11],[12,13],[16,20]], continuous_lines(s7)
        assert continuous_lines(s8, 1) == [4,20], continuous_lines(s7)
        assert continuous_lines(s9, 1) == [4,5], continuous_lines(s9)

    def test_L(self):
        image = self.open_localimg('RGB.jpg')
        for _ in range(1000):
            img = grey_img(image) # 0.462s
            # img = image.convert('L') # 0.14s

    def open_localimg(self, path):
        with open(path,'rb') as image:
            return Image.open(StringIO.StringIO(image.read()))
            

if __name__ == '__main__':
    unittest.main()
