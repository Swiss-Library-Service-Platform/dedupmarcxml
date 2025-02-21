import unittest

from dedupmarcxml.evaluate import *
from dedupmarcxml.briefrecord import XmlBriefRec, JsonBriefRec
from almasru.client import SruClient, SruRecord, SruRequest
import pickle
import os


SruClient.set_base_url('https://swisscovery.slsp.ch/view/sru/41SLSP_NETWORK')


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

    def test_evaluate_titles(self):
        score1 = evaluate_short_titles('Mozrt', 'Mozart')
        self.assertTrue(score1 > 0.9)

        score2 = evaluate_short_titles('Mozart, un compositeur de génie', 'Mozart, un compositeur')
        self.assertTrue(0.8 < score2 < 0.95, f'0.8 < {score2} < 0.95')

        score3 = evaluate_short_titles('Mozart', 'Beethoven')
        self.assertTrue(score3 < 0.5)

        score4 = evaluate_short_titles('Magnifique livre: il adore la Montagne', 'Il adore la Montagne')
        self.assertTrue(score4 > 0.8)

        score4 = evaluate_short_titles(['Ein zwei drei', 'Un deux trois'],
                                       ['Vier fün sechs', 'Un deux trois'])
        self.assertTrue(score4 > 0.9)


    def test_evaluate_creators(self):
        score1 = evaluate_creators(['Mozart'], ['Mozart'])
        self.assertTrue(score1 > 0.9)

        score2 = evaluate_creators(['Mozart, un compositeur de génie'], ['Mozart, un compositeur'])
        self.assertTrue(0.7 < score2 < 0.9, f'0.7 < {score2} < 0.9')

        score3 = evaluate_creators(['Mozart'], ['Beethoven'])
        self.assertTrue(score3 < 0.4)

        score4 = evaluate_creators(['Bernard, Jean', 'Filin, Jules'], ['Bernard, Jean', 'Filin, J.'])
        self.assertTrue(score4 > 0.8)


    def test_evaluate_parent(self):
        parent1 = {"year": 2013,
                   "parts": {
                       "nb": [
                           2013,
                           157,
                           107
                       ],
                       "txt": "2013/107/157"
                   },
                   "title": "Schweizerische Zeitschrift für Religions- und Kulturgeschichte = Revue suisse d'histoire religieuse et culturelle = Rivista svizzera di storia religiosa e culturale"
                   }

        parent2 = {"year": 2013,
                   "parts": {
                       "nb": [
                           2013,
                           157,
                           107
                       ],
                       "txt": "2013/107/157"
                   },
                   "title": "Schweizerische Zeitschrift für Religions- und Kulturgeschichte"
                   }

        score1 = evaluate_parent(parent1, parent2)
        self.assertTrue(score1 > 0.7, f'{score1} > 0.7')


    def test_evaluate_records_similarity_1(self):
        mms_id = '991036265429705501'

        rec = SruRecord(mms_id)
        rec = XmlBriefRec(rec.data)

        sim_score = evaluate_records_similarity(rec, rec)
        score = get_similarity_score(sim_score)
        self.assertGreater(score, 0.99)
        self.assertLess(sim_score['std_nums'], 0.01)

        score = get_similarity_score(sim_score)
        self.assertGreater(score, 0.99)

    def test_evaluate_records_similarity_2(self):
        mms_id1 = '991036265429705501'
        mms_id2 = '991057213849705501'
        rec1 = SruRecord(mms_id1)
        rec1 = XmlBriefRec(rec1.data)
        rec2 = SruRecord(mms_id2)
        rec2 = XmlBriefRec(rec2.data)
        sim_score = evaluate_records_similarity(rec1, rec2)

        self.assertTrue(0.5 < sim_score['titles'] < 0.7, f'0.5 < {sim_score["titles"]} < 0.7')
        self.assertTrue(0.1 < sim_score['parent'] < 0.4, f'0.1 < {sim_score["parent"]} < 0.4')

        score = get_similarity_score(sim_score)
        self.assertTrue(0.4 < score < 0.6, f'0.3 < {score} < 0.5')

    def test_evaluate_records_similarity_3(self):
        mms_id = '991171276160305501' # same mms_id

        with open('data_for_testing/record3.pkl' if os.getcwd().endswith('tests') else 'tests/data_for_testing/record3.pkl', 'rb') as f:
            data = pickle.load(f)
        rec1 = JsonBriefRec(data)
        rec2 = SruRecord(mms_id)
        rec2 = XmlBriefRec(rec2.data)

        sim_score = evaluate_records_similarity(rec1, rec2)
        score = get_similarity_score(sim_score)

        self.assertTrue(0.9 < score <= 1, f'0.9 < {score} <= 1')


if __name__ == '__main__':
    unittest.main()
