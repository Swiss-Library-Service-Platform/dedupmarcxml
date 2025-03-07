import unittest
from dedupmarcxml.score.extent import get_rounded_extent, calc_with_sets, calc_with_sum, calc_notated_music_score

class TestScoreExtent(unittest.TestCase):

    def test_get_rounded_extent(self):
        self.assertEqual(get_rounded_extent({5, 15, 25}), {5, 15, 20, 10})
        self.assertEqual(get_rounded_extent({10, 20, 30}), {10, 20, 30})
        self.assertEqual(get_rounded_extent({1, 2, 3}), {1, 2, 3})
        self.assertEqual(get_rounded_extent({21, 22, 23}), {10, 20})

    def test_calc_with_sets(self):
        self.assertAlmostEqual(calc_with_sets({10, 20, 30}, {10, 20, 30}), 1.0)
        self.assertLess(calc_with_sets({23, 182}, {20, 181}), 0.1)
        self.assertGreater(calc_with_sets({1, 180, 170}, {180, 170}), 0.99)
        self.assertLess(calc_with_sets({10, 20, 30}, {30, 40}), 0.3)
        self.assertGreater(calc_with_sets({15, 190, 200}, {190, 200}), 0.6)

    def test_calc_with_sum(self):
        self.assertGreater(calc_with_sum({10, 200}, {15, 201}), 0.7)
        self.assertAlmostEqual(calc_with_sum({10, 200}, {210}), 1)
        self.assertGreater(calc_with_sum({10, 200}, {212}), 0.9)
        self.assertLess(calc_with_sum({10, 20, 30}, {10, 20}), 0.1)

    def test_calc_notated_music_score(self):
        self.assertLess(calc_notated_music_score('212, 42, 1 / 1 partition (XLII, 212 pages)',
                                                 '212, 42, 1 / 1 Taschenpartitur (XLII, 212 S.)', 1),
                        0.8)
        self.assertGreater(calc_notated_music_score('212, 42, 1 / 1 partition (XLII, 212 pages)',
                                                 '212, 42, 1 / 1 Tschenpartitur (XLII, 212 S.)', 1),
                        0.8)
        self.assertTrue(0.6 < calc_notated_music_score('112, 1 / 1 réduction (112 pages)',
                                                 '1 / 1 Klavierauszug', 0.4) < 0.7,
                        f'calc_notated_music_score("112, 1 / 1 réduction (112 pages)", "1 / 1 Klavierauszug", 4) = {calc_notated_music_score("112, 1 / 1 réduction (112 pages)", "1 / 1 Klavierauszug", 0.4)}')


if __name__ == '__main__':
    unittest.main()