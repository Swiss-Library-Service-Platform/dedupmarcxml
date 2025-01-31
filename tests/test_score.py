import unittest

from dedup.score import evaluate_publishers, evaluate_editions

class TestScore(unittest.TestCase):

    def test_calculate_publishers_score_1(self):
        self.assertTrue(evaluate_publishers('Springer', 'Springer') > 0.9)
        self.assertTrue(0.4 < evaluate_publishers('Springer', 'Springer Nature') < 0.6, f'Springer, Springer , score, should be between 0.4 and 0.6 and it is {evaluate_publishers("Springer", "Springer Nature")}')
        self.assertTrue(evaluate_publishers('Springer Nature Gr.', 'Springer Nature Group') > 0.95, f'Springer Nature Gr., Springer Nature Group, score, should be greater than 0.95 and it is {evaluate_publishers("Springer Nature Gr.", "Springer Nature Group")}')

    def test_calculate_publishers_score_2(self):
        self.assertTrue(evaluate_publishers(['Springer'], ['Payot', 'Springer']) > 0.9)
        self.assertTrue(0.4 < evaluate_publishers('Springer', ['Springer Nature']) < 0.6, f'Springer, Springer , score, should be between 0.4 and 0.6 and it is {evaluate_publishers("Springer", "Springer Nature")}')
        # self.assertTrue(evaluate_publishers('Springer Nature Gr.', 'Springer Nature Group') > 0.95, f'Springer Nature Gr., Springer Nature Group, score, should be greater than 0.95 and it is {evaluate_publishers("Springer Nature Gr.", "Springer Nature Group")}')


    def test_calculate_editions_score(self):
        self.assertGreater(evaluate_editions('2e ed.', 'Deuxième édition'), 0.9)
        self.assertLess(evaluate_editions('3e ed.', 'Deuxième édition'), 0.2)
        self.assertLess(evaluate_editions('3e ed.', 'ed. rev.'), 0.5)

if __name__ == '__main__':
    unittest.main()
