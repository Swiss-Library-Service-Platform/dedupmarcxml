import unittest
from dedupmarcxml.tools import *

class TestTools(unittest.TestCase):

    def test_to_ascii(self):
        self.assertEqual(to_ascii('Café'), 'CAFE')
        self.assertEqual(to_ascii('naïve'), 'NAIVE')
        self.assertEqual(to_ascii('résumé'), 'RESUME')
        self.assertEqual(to_ascii('ça c\'est bien'), 'CA C\'EST BIEN')

    def test_remove_special_chars(self):
        self.assertEqual(remove_special_chars('Hello, World!'), 'Hello World')
        self.assertEqual(remove_special_chars('Hello... World!', keep_dot=True), 'Hello... World')
        self.assertEqual(remove_special_chars('Hello... World!', keep_dot=False), 'Hello World')

    def test_solve_abbreviations(self):
        self.assertEqual(solve_abbreviations('univ.', 'university'), ('university', 'university'))
        self.assertEqual(solve_abbreviations('prof.', 'professor'), ('professor', 'professor'))

    def test_evaluate_text_similarity(self):
        self.assertEqual(evaluate_text_similarity('SPRINGER', 'SPRINGER'), 1)

        self.assertLess(evaluate_text_similarity('SPRINGER', 'SPRINGER NATURE'), 1)
        self.assertGreater(evaluate_text_similarity('SPRINGER', 'SPRINGER NATURE'), 0.5)

        self.assertLess(evaluate_text_similarity('ED. PAYOT', 'EDITIONS PAYOT'), 1)
        self.assertGreater(evaluate_text_similarity('ED. PAYOT', 'EDITIONS PAYOT'), 0.5)


if __name__ == '__main__':
    unittest.main()