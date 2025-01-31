"""
250$$a

create dictionary with numbers in all languages

create list of stop words
"""

import re
import pickle
import os
import numpy as np
import Levenshtein
from typing import List
from dedup import tools


_editions_data = pickle.load(open(os.path.join(os.path.dirname(__file__), 'data/editions_data.pickle'), 'rb'))


def normalize_edition(edition: str) -> str:
    """Normalize publisher names and calculate a factor to correct small differences

    This function normalizes the edition statement, solves abbreviations.

    :param edition: string containing publisher of the first record

    :return: list of numbers found.
    """

    # Normalize edition statement
    edition = tools.to_ascii(edition)
    edition = tools.remove_special_chars(edition, keep_dot=True)

    for k in _editions_data.keys():
        edition = re.sub(r'\b' + k + r'\b', str(_editions_data[k]), edition)

    # Find all numbers in the edition statement
    numbers = sorted([int(f) for f in re.findall(r'\d+', edition)])
    print(';'.join([str(n) for n in numbers] + [edition]))
    return ';'.join([str(n) for n in numbers] + [edition]) if len(numbers) > 0 else edition


def evaluate_norm_editions(ed1: str, ed2: str) -> float:
    """Evaluate similarity of editions

    It uses a multilingual dictionary to fetch the edition number and
    compare it. Other textual elements are of less importance.

    :param ed1: string containing edition of the first record
    :param ed2: string containing edition of the second record

    :return: float with matching score
    """
    # If all editions statements are numbers, we can compare numbers
    if re.search(r'\d', ed1) is not None and re.search(r'\d', ed2) is not None:

        # We ignore the complete statement at the end
        nb_list_1 = set(ed1.split(';')[:-1])
        nb_list_2 = set(ed2.split(';')[:-1])

        score_nb = len(set.intersection(nb_list_1, nb_list_2)) / max(len(nb_list_1), len(nb_list_2))
        return score_nb

    return -1
