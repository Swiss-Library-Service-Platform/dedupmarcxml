import numpy as np
from dedupmarcxml import tools
import re

extent_types = {
    'reduction': ['REDUCTION', 'AUSZUG', 'RIDUZIONE'],
    'pocket': ['TASCHE', 'POCHE', 'POCKET'],
    'orchestra': ['AUFFUEHRUNG', 'ORCHESTR'],
    'part': ['PARTIE', r'\bPART\b', 'STIMME']
}


def get_rounded_extent(extent):
    """Simple extent normalization to get rounded values"""

    return {v if v < 20 else n * 10 for v in extent for n in (v // 10 - 1, v // 10)}


def calc_with_sets(extent1, extent2):
    """Calculate score for extent comparison

    It uses a factor to give more importance to large numbers.

    :param extent1: set of integers
    :param extent2: set of integers

    :return: float with matching score"""
    score = len(set.intersection(extent1, extent2)) / len(set.union(extent1, extent2))

    factor = np.prod(list(set.intersection(extent1, extent2))) / np.prod(list(set.union(extent1, extent2, [1.01])))

    return score + (1 - score) * factor


def calc_with_sum(extent1, extent2):
    """Calculate score for extent sum comparison

    :param extent1: set of integers
    :param extent2: set of integers

    :return: float with matching score"""

    if sum(extent1) + sum(extent2) <= 0:
        return 0

    score = np.clip(
        (np.abs(sum(extent1) - sum(extent2)) / (sum(extent1) + sum(extent2))) * 15
        , 0, 1)

    return 1 - score


def calc_notated_music_score(extent1, extent2, score):
    """Calculate score for notated music extent comparison

    We use a dictionary with extent types and their values to compare the two extents.
    A penalty is applied when a category word is available in only one record.
    A bonus is applied when in the two records a word of the category is available.
    No bonus is applied when a penalty is applied.

    :param extent1: text of the extent of the first record
    :param extent2: text of the extent of the second record
    :param score: float with matching score

    :return: float with matching score"""
    norm_extent1 = tools.to_ascii(extent1)
    norm_extent2 = tools.to_ascii(extent2)
    result = {k:{'rec1': False, 'rec2': False} for k in extent_types.keys()}
    for extent_type, extent_values in extent_types.items():
        for extent_value in extent_values:
            if re.search(extent_value, norm_extent1) is not None:
                result[extent_type]['rec1'] = True
            if re.search(extent_value, norm_extent2) is not None:
                result[extent_type]['rec2'] = True

    penalty = 0
    bonus = 0

    # Calculate penalty and bonus
    for t in result.values():
        if t['rec1'] != t['rec2']:
            penalty += 1
        elif t['rec1'] is True and t['rec2'] is True:
            bonus += 1

    # Apply penalty
    score = score * 0.75 ** (penalty ** 2)

    # No bonus if penalty is applied
    if bonus > 0 and penalty == 0:
        score = score ** (0.5 / bonus)

    return score
