import unittest

from dedup.score_editions import *

class TestScorePublishers(unittest.TestCase):

    def test_normalize_editions(self):
        ed = normalize_edition('17. Auflage, Originalausgabe')
        self.assertEqual(ed, '17;17. AUFLAGE ORIGINALAUSGABE')

        ed = normalize_edition('First Edition 1996')
        self.assertEqual(ed, '1;1996;1 EDITION 1996')

        ed = normalize_edition('Nachdr. der 2. vermehrten Aufl., Leipzig 1854 stattdessen auf dem Originaltitel unzutreffend 1853')
        self.assertEqual(ed, '2;1853;1854;NACHDR. DER 2. VERMEHRTEN AUFL. LEIPZIG 1854 STATTDESSEN AUF DEM ORIGINALTITEL UNZUTREFFEND 1853')

        ed = normalize_edition('Harrison\'s edition')
        self.assertEqual(ed, 'HARRISON S EDITION')

    def test_evaluate_norm_editions(self):
        score = evaluate_norm_editions('17;17. AUFLAGE ORIGINALAUSGABE', '16;16. AUFLAGE ORIGINALAUSGABE')
        self.assertLess(score, 0.1)

        score = evaluate_norm_editions('17;17. AUFLAGE ORIGINALAUSGABE', '17;17. AUFLAGE')
        self.assertGreater(score, 0.9)

        score = evaluate_norm_editions('2;Sec. AUFLAGE ORIGINALAUSGABE', '2;2. AUFLAGE')
        self.assertGreater(score, 0.9)
