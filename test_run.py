import unittest
from oa import OAini, HBCDC

class OAtest(unittest.TestCase):
    ini = OAini

    def test_gethbcdcMail(self):
        """
        hbcdc get a mail
        """
        u, p = self.ini.get('hbcdc', 'user'), self.ini.get('hbcdc', 'passwd')
        hbcdc = HBCDC(u, p)
        ids = ['bf872eac-54f4-4ced-9236-6fa1f3d2d202',
        'de3cd6a9-c480-4888-b636-afd9c46ea67f',
        '483658f1-9716-42f9-9f42-56c7c0e94651']
        data = [hbcdc.mail_parser(id) for id in ids]
        for d in data:
            hbcdc.save_doc(d)

if __name__ == "__main__":
    unittest.main()