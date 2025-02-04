import unittest

from dedup.score import *
from dedup.score_editions import *
from dedup.briefrecord import BriefRecFactory, BriefRec

class TestScore(unittest.TestCase):

    def test_calculate_publishers_score_1(self):
        self.assertTrue(evaluate_publishers('Springer', 'Springer') > 0.9)
        self.assertTrue(0.4 < evaluate_publishers('Springer', 'Springer Nature') < 0.6)
        self.assertTrue(evaluate_publishers('Springer Nature Gr.', 'Springer Nature Group') > 0.95)

    def test_calculate_publishers_score_2(self):
        self.assertTrue(evaluate_publishers(['Springer'], ['Payot', 'Springer']) > 0.9)
        self.assertTrue(0.4 < evaluate_publishers('Springer', ['Springer Nature']) < 0.6)

    def test_calculate_editions_score(self):
        self.assertGreater(evaluate_editions([{'nb': [2], 'txt': '2e ed.'}],
                                             [{'nb': [2], 'txt': 'Deuxième édition'}]), 0.9)
        self.assertGreater(evaluate_editions([{'nb': [2], 'txt': '2e ed.'}, {'nb': [], 'txt': 'ed. augmentée'}],
                                             [{'nb': [2], 'txt': 'Deuxième édition'}]), 0.9)
        self.assertLess(evaluate_editions([{'nb': [3], 'txt': '3e éd.'}],
                                          [{'nb': [2], 'txt': 'Deuxième édition'}]), 0.3)
        self.assertLess(evaluate_editions([{'nb': [3], 'txt': '3e éd.'}],
                                          [{'nb': [], 'txt': 'ed. rev.'}]), 0.6)

    def test_caculate_extents_score(self):
        self.assertGreater(evaluate_extent({'nb': [300], 'txt': '300 p.'},
                                           {'nb': [300], 'txt': '300 pages'}), 0.9)
        self.assertGreater(evaluate_extent({'nb': [300], 'txt': '300 p.'},
                                           {'nb': [301], 'txt': '301 p.'}), 0.85)
        self.assertGreater(evaluate_extent({'nb': [300], 'txt': '300 p.'},
                                           {'nb': [15, 285], 'txt': '15 p., 285 p.'}), 0.85)
        self.assertGreater(evaluate_extent({'nb': [20, 300], 'txt': '20 p., 300 p.'},
                                           {'nb': [21, 301], 'txt': '21 p., 301 p.'}), 0.8)
        self.assertLess(evaluate_extent({'nb': [300], 'txt': '300 p.'},
                                        {'nb': [280], 'txt': '280 p.'}), 0.4)

    def test_calculate_years_score(self):
        self.assertGreater(evaluate_years(2000, 2000), 0.9)
        self.assertGreater(evaluate_years(2000, 2001), 0.8)
        self.assertGreater(evaluate_years(2000, 2002), 0.6)
        self.assertLess(evaluate_years(2000, 2005), 0.4)
        self.assertLess(evaluate_years(2000, 2006), 0.3)
        self.assertLess(evaluate_years(2000, 2007), 0.3)

    def test_calculate_years_start_and_end_score(self):
        score1 = evaluate_years_start_and_end({'y1': [2000, 2005], 'y2': 2000}, {'y1': [2000], 'y2': 2000})
        self.assertGreater(score1, 0.9)

        score2 = evaluate_years_start_and_end({'y1': [2000, 2001], 'y2': 2000}, {'y1': [2000]})
        self.assertTrue(0.8 < score2 < 0.95, f'0.8 < {score2} < 0.95')

        score3 = evaluate_years_start_and_end({'y1': [2000, 2001], 'y2': 2011}, {'y1': [2000, 2001], 'y2': 2010})
        self.assertTrue(0.9 < score3 < 0.98, f'0.9 < {score3} < 0.98')

        score4 = evaluate_years_start_and_end({'y1': [2001]}, {'y1': [2000]})
        self.assertTrue(0.7 < score4 < 0.9, f'0.7 < {score4} < 0.9')

    def test_evaluate_languages(self):
        self.assertTrue(evaluate_languages(['eng'], ['eng']) > 0.9)
        self.assertTrue(0.5 < evaluate_languages(['eng'], ['fr', 'eng']) < 0.7)
        self.assertTrue(0.85 < evaluate_languages(['eng'], ['eng', 'fr']) < 0.95)
        self.assertTrue(evaluate_languages(['eng'], ['ger']) < 0.5)

    def test_evaluate_identifiers(self):
        score1 = evaluate_identifiers(['123'], ['123'])
        self.assertTrue(score1 > 0.9)

        score2 = evaluate_identifiers(['123'], ['123', '456'])
        self.assertTrue(0.9 < score2 < 1, f'0.9 < {score2} < 1')

        score3 = evaluate_identifiers(['123'], ['456', '123', '222'])
        self.assertTrue(0.8 < score3 < 0.96, f'0.8 < {score3} < 0.96')

        score4 = evaluate_identifiers(['123'], ['456'])
        self.assertTrue(score4 < 0.3)

if __name__ == '__main__':
    unittest.main()
