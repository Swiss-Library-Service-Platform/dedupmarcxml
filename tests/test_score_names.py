import unittest

from dedupmarcxml.score.names import *

class TestScoreNames(unittest.TestCase):

    def test_evaluate_lists_names(self):
        score1 = evaluate_lists_names(['Jean Dupont'], ['Jean Dupont'])
        self.assertGreater(score1, 0.9)

        score2 = evaluate_lists_names(['Jean Dupont'], ['Jean Dupond'])
        self.assertTrue(0.6 < score2 < 0.8, f'0.6 < {score2} < 0.8')

        score3 = evaluate_lists_names(['Jean Dubont', 'Martine, Lise'],
                                      ['Jean Dupond', 'Martinet, Henri'])
        self.assertTrue(0.2 < score3 < 0.4, f'0.5 < {score3} < 0.7')


    def test_evaluate_names(self):
        score1 = evaluate_names('Jean Dupont', 'Jean Dupont')
        self.assertGreater(score1, 0.9)

        score2 = evaluate_names('Jean Dupont', 'Jean Dupond')
        self.assertTrue(0.6 < score2 < 0.8, f'0.6 < {score2} < 0.8')

        score3 = evaluate_names('Jean Dubont', 'Jean Dupond')
        self.assertTrue(0.3 < score3 < 0.5, f'0.3 < {score3} < 0.5')


if __name__ == '__main__':
    unittest.main()