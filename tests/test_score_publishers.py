import unittest

from dedupmarcxml.score.publishers import *

class TestScorePublishers(unittest.TestCase):

    def test_normalize_publishers(self):
        pub1, pub2, factor = normalize_publishers('Springer', 'Springer')
        self.assertEqual(pub1, 'SPRINGER')
        self.assertEqual(pub2, 'SPRINGER')
        self.assertEqual(factor, 1)

        pub1, pub2, factor = normalize_publishers('Springer', 'Springer Nature')
        self.assertEqual(pub1, 'SPRINGER')
        self.assertEqual(pub2, 'SPRINGER NATURE')
        self.assertEqual(factor, 1)

        pub1, pub2, factor = normalize_publishers('éd. Payot', 'Editions Payot')
        self.assertEqual(pub1, 'EDITIONS PAYOT')
        self.assertEqual(pub2, 'EDITIONS PAYOT')
        self.assertEqual(factor, 1)

        pub1, pub2, factor = normalize_publishers('PUF', 'Presses Universitaire de France')
        self.assertEqual(pub1, 'PRESSES UNIVERSITAIRE DE FRANCE')
        self.assertEqual(pub2, 'PRESSES UNIVERSITAIRE DE FRANCE')
        self.assertLess(factor, 1)
        self.assertGreater(factor, 0.9)

        pub1, pub2, factor = normalize_publishers('A-R Editions', 'A-R Editions, Inc')
        self.assertEqual(pub1, 'A-R EDITIONS')
        self.assertEqual(pub2, 'A-R EDITIONS INC')
        self.assertEqual(factor, 1)

    def test_evaluate_publishers_vect(self):
        self.assertTrue(evaluate_publishers_vect('ED PAYOT', 'PAYOT') > 0.9)
        self.assertTrue(evaluate_publishers_vect('PAYOT GENEVE', 'PAYOT ZURICH') > 0.9)
        self.assertTrue(evaluate_publishers_vect('PAYO GENEVE', 'PAYOT GENEVE') < 0.5)
        self.assertTrue(evaluate_publishers_vect('A-R EDITIONS', 'A-R EDITIONS INC') > 0.9)

    def test_normalize_txt(self):
        self.assertEqual(normalize_txt('Springer'), 'SPRINGER')
        self.assertEqual(normalize_txt('Springer Nature'), 'SPRINGER NATURE')
        self.assertEqual(normalize_txt('éd. Payot', keep_dot=False), 'ED PAYOT')
        self.assertEqual(normalize_txt('éd. Payot', keep_dot=True), 'ED. PAYOT')

    def test_correct_small_differences(self):
        pub1, pub2, factor = correct_small_differences('SPRINGER', 'SPRINGER')
        self.assertEqual(pub1, 'SPRINGER')
        self.assertEqual(pub2, 'SPRINGER')
        self.assertEqual(factor, 1)

        pub1, pub2, factor = correct_small_differences('SPRINGER NATURE', 'SPINGER NATURE')
        self.assertEqual(pub1, 'SPRINGER NATURE')
        self.assertEqual(pub2, 'SPRINGER NATURE')
        self.assertLess(factor, 1)
        self.assertGreater(factor, 0.9)

if __name__ == '__main__':
    unittest.main()