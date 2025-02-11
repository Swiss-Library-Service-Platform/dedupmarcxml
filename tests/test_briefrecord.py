from almasru.client import SruClient, SruRecord, SruRequest
from almasru import config_log
import unittest
from dedupmarcxml import BriefRec
import shutil

config_log()
SruClient.set_base_url('https://swisscovery.slsp.ch/view/sru/41SLSP_NETWORK')

class TestSruClient(unittest.TestCase):
    def test_create_brief_record_1(self):
        mms_id = '991055037209705501' # Book physical
        rec = SruRecord(mms_id)
        rec = BriefRec(rec.data)

        self.assertEqual(rec.data['extent']['nb'][0], 764)
        self.assertEqual(rec.data['format']['access'], 'Physical')
        self.assertEqual(rec.data['editions'][0]['nb'][0], 2)

    def test_create_brief_record_2(self):
        mms_id = '991171854084705501' # Braille
        rec = SruRecord(mms_id)
        rec = BriefRec(rec.data)
        self.assertEqual(rec.data['format']['type'], 'Book')
        self.assertEqual(rec.data['format']['access'], 'Braille')
        self.assertEqual(rec.data['years']['y2'], 2020)

    def test_create_brief_record_3(self):
        mms_id = '991039410659705501'  # Score physical
        rec = SruRecord(mms_id)
        rec = BriefRec(rec.data)

        self.assertEqual(rec.data['extent']['nb'], [86, 1])
        self.assertEqual(rec.data['format']['type'], 'Notated Music')
        self.assertEqual(rec.data['years']['y1'][0], 1926)
        self.assertTrue('H 29,265' in rec.data['std_nums'])

    def test_create_brief_record_4(self):
        mms_id = '991144737319705501'  # Article physical
        rec = SruRecord(mms_id)
        rec = BriefRec(rec.data)

        self.assertTrue(rec.data['format']['analytical'])
        self.assertEqual(rec.data['parent']['year'], 1985)
        self.assertTrue('Mozart' in rec.data['short_titles'], rec.data['short_titles'])


    def test_create_brief_record_5(self):
        mms_id = '991170632470305501'  # Film online
        rec = SruRecord(mms_id)
        rec = BriefRec(rec.data)

        self.assertEqual(rec.data['format']['type'], 'Video')
        self.assertEqual(rec.data['format']['access'], 'Online')
        self.assertEqual(rec.data['extent']['nb'], [51, 1])
        self.assertEqual(rec.data['languages'], ['eng'])

    def test_create_brief_record_6(self):
        mms_id = '991019884739705501' # multi lingual book
        rec = SruRecord(mms_id)
        rec = BriefRec(rec.data)
        self.assertEqual(set(rec.data['languages']), {'lat', 'fre'})
        self.assertTrue('Collection des Universités de France' in rec.data['series'])

    def test_create_brief_record_7(self):
        mms_id = '991171135704605501' # multi titles
        rec = SruRecord(mms_id)
        rec = BriefRec(rec.data)

        self.assertTrue('La coopération transfrontalière après la pandémie' in [t['m'] for t in rec.data['titles']],
                        [t['m'] for t in rec.data['titles']])
        self.assertTrue('Peter Lang' in rec.data['publishers'])


    # def test_create_brief_record_8(self):
    #     mms_id = '991036265429705501'
    #
    #     rec = SruRecord(mms_id)
    #     rec = BriefRec(rec.data)
    #     print(rec)