import numpy as np

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