import os

from almasru.client import SruClient, SruRecord, SruRequest
from almasru import config_log
import unittest
from dedupmarcxml import XmlBriefRec, JsonBriefRec
import pickle

config_log()
SruClient.set_base_url('https://swisscovery.slsp.ch/view/sru/41SLSP_NETWORK')

class TestSruClient(unittest.TestCase):
    def test_create_brief_record_1(self):
        mms_id = '991055037209705501' # Book physical
        rec = SruRecord(mms_id)
        rec = XmlBriefRec(rec.data)

        self.assertEqual(rec.data['extent']['nb'][0], 764)
        self.assertEqual(rec.data['format']['access'], 'Physical')
        self.assertEqual(rec.data['editions'][0]['nb'][0], 2)

    def test_create_brief_record_2(self):
        mms_id = '991171854084705501' # Braille
        rec = SruRecord(mms_id)
        rec = XmlBriefRec(rec.data)
        self.assertEqual(rec.data['format']['type'], 'Book')
        self.assertEqual(rec.data['format']['access'], 'Braille')
        self.assertEqual(rec.data['years']['y2'], 2020)

    def test_create_brief_record_3(self):
        mms_id = '991039410659705501'  # Score physical
        rec = SruRecord(mms_id)
        rec = XmlBriefRec(rec.data)

        self.assertEqual(rec.data['extent']['nb'], [86, 1])
        self.assertEqual(rec.data['format']['type'], 'Notated Music')
        self.assertEqual(rec.data['years']['y1'][0], 1926)
        self.assertTrue('H 29,265' in rec.data['std_nums'])

    def test_create_brief_record_4(self):
        mms_id = '991144737319705501'  # Article physical
        rec = SruRecord(mms_id)
        rec = XmlBriefRec(rec.data)

        self.assertTrue(rec.data['format']['analytical'])
        self.assertEqual(rec.data['parent']['year'], 1985)
        self.assertTrue('Mozart' in rec.data['short_titles'], rec.data['short_titles'])


    def test_create_brief_record_5(self):
        mms_id = '991170632470305501'  # Film online
        rec = SruRecord(mms_id)
        rec = XmlBriefRec(rec.data)

        self.assertEqual(rec.data['format']['type'], 'Video')
        self.assertEqual(rec.data['format']['access'], 'Online')
        self.assertEqual(rec.data['extent']['nb'], [51, 1])
        self.assertEqual(rec.data['languages'], ['eng'])

    def test_create_brief_record_6(self):
        mms_id = '991019884739705501' # multi lingual book
        rec = SruRecord(mms_id)
        rec = XmlBriefRec(rec.data)
        self.assertEqual(set(rec.data['languages']), {'lat', 'fre'})
        self.assertTrue('Collection des Universités de France' in rec.data['series'])

    def test_create_brief_record_7(self):
        mms_id = '991171135704605501' # multi titles
        rec = SruRecord(mms_id)
        rec = XmlBriefRec(rec.data)

        self.assertTrue('La coopération transfrontalière après la pandémie' in [t['m'] for t in rec.data['titles']],
                        [t['m'] for t in rec.data['titles']])
        self.assertTrue('Peter Lang' in rec.data['publishers'])

    def test_json_brief_record_1(self):

        with open('data_for_testing/record1.pkl' if os.getcwd().endswith('tests') else 'tests/data_for_testing/record1.pkl', 'rb') as f:
            data = pickle.load(f)
        rec = JsonBriefRec(data)

        self.assertEqual(rec.data['extent']['nb'][0], 269)
        self.assertEqual(rec.data['titles'][0]['m'], 'How architects write')
        self.assertEqual(rec.data['editions'][0]['nb'][0], 2)

    def test_json_brief_record_2(self):

        with open('data_for_testing/record2.pkl' if os.getcwd().endswith('tests') else 'tests/data_for_testing/record2.pkl', 'rb') as f:
            data = pickle.load(f)
        rec = JsonBriefRec(data)

        self.assertEqual(rec.data['years']['y1'][0], 2015)
        self.assertEqual(rec.data['titles'][0]['m'], "Bourdieu's theory of social fields")
        self.assertEqual(rec.data['titles'][0]['s'], 'concepts and applications')
        self.assertEqual(rec.data['editions'][0]['nb'][0], 1)

    def test_json_brief_record_3(self):

        with open('data_for_testing/record3.pkl' if os.getcwd().endswith('tests') else 'tests/data_for_testing/record3.pkl', 'rb') as f:
            data = pickle.load(f)
        rec = JsonBriefRec(data)

        self.assertEqual(rec.data['years']['y1'][0], 1981)
        self.assertEqual(rec.data['parent']['title'], 'Brugger Neujahrsbl\u00e4tter')
        self.assertEqual(rec.data['parent']['parts']['nb'][1], 91)
        self.assertEqual(rec.data['languages'][0], 'ger')
        self.assertEqual(rec.data['creators'][1], 'Sommer, Werner')
