import numpy as np
import Levenshtein
from typing import List

from dedupmarcxml import tools
import re

def evaluate_lists_names(names1: List[str], names2: List[str]) -> float:
    """evaluate_lists_names(names1: List[str], names2: List[str]) -> float
    Return the result of the best pairing authors.

    The function test all possible pairings and return the max value.

    :param names1: list of names to compare
    :param names2: list of names to compare

    :return: similarity score between two lists of names as float
    """

    if len(names1) < len(names2):
        names2, names1 = (names1, names2)

    if len(names1) < 5:

        unique_combinations = tools.get_unique_combinations(names1, names2)

        return max([np.mean([evaluate_names(*p) for p in comb]) for comb in unique_combinations])
    else:
        # When more than 4 names => not possible to test all combinations
        # Find only the best matches
        scores = []
        for n2 in names2:
            s_max = -1
            n1_temp = None
            for n1 in names1:
                s = evaluate_names(n1, n2)
                if s > s_max:
                    s_max = s
                    n1_temp = n1

            # Remove the best match to avoid to use it twice
            names1.remove(n1_temp)
            scores.append(s_max)

        # Return only the value of the 4 best matches
        return np.mean(sorted(scores, reverse=True)[:4])


def evaluate_names(name1: str, name2: str) -> float:
    """evaluate_names(name1: str, name2: str) -> float
    Return the result of the evaluation of similarity of two names.

    :param name1: name to compare
    :param name2: name to compare

    :return: similarity score between two names as float
    """
    names1 = [tools.to_ascii(re.sub(r'\W', '', n).lower())
              for n in name1.split()]
    names2 = [tools.to_ascii(re.sub(r'\W', '', n).lower())
              for n in name2.split()]

    names1 = [n for n in names1 if n != '']
    names2 = [n for n in names2 if n != '']

    if len(names1) > len(names2):
        names1, names2 = (names2, names1)

    names1 += [''] * (len(names2) - len(names1))

    scores = []
    already_used_n2 = []
    for r1, n1 in enumerate(names1):
        temp_scores = []
        for r2, n2 in enumerate(names2):
            if r2 in already_used_n2:
                continue
            temp_n1, temp_n2 = (n1, n2) if len(n1) >= len(n2) else (n2, n1)
            if len(temp_n2) <= 2:
                temp_scores.append((
                    (Levenshtein.distance(temp_n1[:len(temp_n2)], temp_n2, weights=(1, 1, 1)) * 4 + 0.2 * abs(r1 - r2) + len(
                        temp_n1) - len(temp_n2)) / max([len(n2), len(n1)]), r2)
                )
            else:
                temp_scores.append((
                    (Levenshtein.distance(temp_n1, temp_n2, weights=(1, 1, 1)) * 4 + 0.2 * abs(r1 - r2) + len(temp_n1) - len(
                        temp_n2)) / max([len(n2), len(n1)]), r2)
                )
                # print(temp_n1, temp_n2, distance(temp_n1, temp_n2[:len(temp_n1)], weights=(1, 1, 1)) * 3)

        temp_scores = sorted(temp_scores, key=lambda x: x[0])
        if n1 == '':
            scores.append((n1, names2[temp_scores[0][1]], 0.2))
        else:
            scores.append((n1, names2[temp_scores[0][1]], temp_scores[0][0] ** 2))
        already_used_n2.append(temp_scores[0][1])

    return 1 / (sum([s[2] for s in scores]) + 1)