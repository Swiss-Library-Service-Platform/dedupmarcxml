"""
Module to evaluate similarity between records

This module is the entry point to evaluate similarity between records. It uses
different submodules to evaluate different fields.
"""
from dedup import score_publishers, score_editions, score_extent
import re
from dedup import tools
from functools import wraps
from typing import Optional, Union, List, Callable, Dict
from dedup.briefrecord import BriefRec


def handle_values_lists(func: Callable) -> Callable:
    """
    Decorator to handle lists of values instead of single strings.
    It compares each value from the first list with each value from the second list
    and returns the maximum score found, with small penalty for each value not matched.
    """
    @wraps(func)
    def wrapper(values1: List[str]|str, values2: List[str]|str) -> float:
        if not isinstance(values1, list):
            values1 = [values1]
        if not isinstance(values2, list):
            values2 = [values2]

        max_score = 0.0

        # Compare each value from the first list with each value from the second list
        for p1 in values1:
            for p2 in values2:
                current_score = func(p1, p2)
                if current_score > max_score:
                    max_score = current_score

        return max_score

    return wrapper


def handle_missing_values(default_score: float = 0.2, key=None) -> Callable:
    """
    Decorator to handle missing or invalid input values.
    If either input is None or an empty string/list, it returns a default score.

    :param default_score: The score to return if input is missing or invalid.
    :param key: The key to use to check for missing values in a dictionary.

    :return: The decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            values1: Optional[Union[str, List[str], Dict]],
            values2: Optional[Union[str, List[str], Dict]]
        ) -> float:

            if tools.is_empty(values1, key=key) and tools.is_empty(values2, key=key):
                return 0.0
            elif tools.is_empty(values1, key=key) or tools.is_empty(values2, key=key):
                return default_score / 2

            # If inputs are valid, call the original function
            result = func(values1, values2)
            return result * (1 - default_score) + default_score

        return wrapper

    return decorator

@handle_missing_values()
def evaluate_format(format1: str, format2: str) -> float:
    """Evaluate similarity of formats

    :param format1: string containing format of the first record
    :param format2: string containing format of the second record

    :return: float with matching score
    """
    return tools.evaluate_text_similarity(format1, format2)

@handle_missing_values()
def evaluate_languages(lang1: List[str], lang2: List[str]) -> float:
    """Evaluate similarity of languages

    :param lang1: list of languages of the first record
    :param lang2: list of languages of the second record

    :return: float with matching score
    """
    score = len(set.intersection(set(lang1), set(lang2))) / len(set.union(set(lang1), set(lang2)))
    if lang1[0] == lang2[0]:
        score = 0.7 + 0.3 * score
    return score


@handle_values_lists
@handle_missing_values()
def evaluate_publishers(pub1: str, pub2: str) -> float:
    """Evaluate publishers using a vectorized system

    :param pub1: string containing publisher of the first record
    :param pub2: string containing publisher of the second record

    :return: float with matching score
    """

    # We normalize the publishers and calculate a factor
    pub1, pub2, factor = score_publishers.normalize_publishers(pub1, pub2)

    # We calculate vectorized similarity
    score_vect = score_publishers.evaluate_publishers_vect(pub1, pub2)

    # we correct the result with a factor granted by misspelling test
    return score_vect * factor


@handle_values_lists
@handle_missing_values(key='txt')
def evaluate_editions(ed1: Dict, ed2: Dict) -> float:
    """Evaluate similarity of editions

    It uses a multilingual dictionary to fetch the edition number and
    compare it. Other textual elements are of less importance.

    :param ed1: string containing edition of the first record
    :param ed2: string containing edition of the second record

    :return: float with matching score
    """

    score_txt = tools.evaluate_text_similarity(ed1['txt'], ed2['txt'])
    score_numbers = score_editions.evaluate_norm_editions(ed1['nb'], ed2['nb'])

    if score_numbers != -1:
        return (score_txt + score_numbers * 9) / 10
    else:
        return score_txt


@handle_missing_values(key='nb')
def evaluate_extent(extent1_dict: Dict, extent2_dict: Dict) -> float:
    """Evaluate similarity of extent

    Idea is to calculate three scores and ponderate them:
    - score1: extent comparison (strict)
    - score2: extent comparison (rounded)
    - score3: extent sum comparison

    :param extent1_dict: dictionary containing extent of the first record
    :param extent2_dict: dictionary containing extent of the second record

    :return: float with matching score
    """

    extent1 = extent1_dict['nb']
    extent2 = extent2_dict['nb']

    extent_set1 = set(extent1)
    extent_set2 = set(extent2)
    score1 = score_extent.calc_with_sets(extent_set1, extent_set2)

    rounded_extent1 = score_extent.get_rounded_extent(extent_set1)
    rounded_extent2 = score_extent.get_rounded_extent(extent_set2)
    score2 = score_extent.calc_with_sets(rounded_extent1, rounded_extent2)

    score3 = score_extent.calc_with_sum(extent1, extent2)

    # If sum is very different of other evaluation and very high we consider it as a good match. Maybe the librarians
    # added parts of the book in the extent.

    if score3 - score1 > 0.5 and score3 > 0.95 and sum(extent1) + sum(extent2) > 100:
        return (score1 + score2 + score3 * 10) / 12

    return (score1 + score2 + score3) / 3

@handle_values_lists
@handle_missing_values()
def evaluate_years(year1: int, year2: int) -> float:
    """Evaluate similarity of years

    :param year1: integer containing year of the first record
    :param year2: integer containing year of the second record

    :return: float with matching score
    """
    return 1 / ((abs(year1 - year2) * .5) ** 2 + 1)

@handle_missing_values(key='y1')
def evaluate_years_start_and_end(year1: Dict, year2: Dict) -> float:
    """Evaluate similarity of years

    :param year1: dictionary containing start and end year of the first record
    :param year2: dictionary containing start and end year of the second record

    :return: float with matching score
    """
    score_start = evaluate_years(year1['y1'], year2['y1'])

    score_end = evaluate_years(year1.get('y2'), year2.get('y2'))
    if score_end == 0:
        return score_start
    elif score_end == 0.1:
        return score_start * 0.9
    else:
        return (score_start * 3 + score_end) / 4


@handle_missing_values()
def evaluate_identifiers(ids1: List[str], ids2: List[str]) -> float:
    """Return the result of the evaluation of similarity of two lists of identifiers.

    :param ids1: list of identifiers to compare
    :param ids2: list of identifiers to compare

    :return: similarity score between two lists of identifiers as float
    """
    ids1 = set(ids1)
    ids2 = set(ids2)
    if len(set.union(ids1, ids2)) > 0:
        score = len(set.intersection(ids1, ids2)) / len(set.union(ids1, ids2))
        return score ** .05 if score > 0 else 0
    else:
        return 0


def evaluate_records_similarity(rec1:BriefRec, rec2:BriefRec) -> Dict[str, float]:
    """Evaluate similarity between two records

    :param rec1: BriefRecord object
    :param rec2: BriefRecord object

    :return: float with matching score
    """
    # We evaluate the similarity of the formats
    score_format = evaluate_format(rec1.data['format'], rec2.data['format'])

    # We evaluate the similarity of the languages
    score_lang = evaluate_languages(rec1.data['languages'], rec2.data['languages'])

    # We evaluate the similarity of the publishers
    score_pub = evaluate_publishers(rec1.data['publishers'], rec2.data['publishers'])

    # We evaluate the similarity of the editions
    score_ed = evaluate_editions(rec1.data['editions'], rec2.data['editions'])

    # We evaluate the similarity of the extent
    score_ext = evaluate_years(rec1.data['extent'], rec2.data['extent'])

    # We evaluate the similarity of the years
    score_yr = evaluate_years_start_and_end(rec1.data['years'], rec2.data['years'])

    # We evaluate the similarity of the standard numbers
    score_std_nums = evaluate_identifiers(rec1.data['std_nums'], rec2.data['std_nums'])

    # We evaluate the similarity of system numbers
    score_sys_nums = evaluate_identifiers(rec1.data['sys_nums'], rec2.data['sys_nums'])

    return {'format': score_format,
            'languages': score_lang,
            'publishers': score_pub,
            'editions': score_ed,
            'extent': score_ext,
            'years': score_yr,
            'std_nums': score_std_nums,
            'sys_nums': score_sys_nums}

if __name__ == "__main__":
    pass