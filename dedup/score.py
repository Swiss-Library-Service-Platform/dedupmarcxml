"""
Module to evaluate similarity between records

This module is the entry point to evaluate similarity between records. It uses
different submodules to evaluate different fields.
"""
from dedup import score_publishers, score_editions
import re
from dedup import tools
from functools import wraps
from typing import Optional, Union, List, Callable


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

        # Compare each publisher from the first list with each publisher from the second list
        for p1 in values1:
            for p2 in values2:
                current_score = func(p1, p2)
                if current_score > max_score:
                    max_score = current_score

        return max_score

    return wrapper




def handle_missing_values(default_score: float = 0.2) -> Callable:
    """
    Decorator to handle missing or invalid input values.
    If either input is None or an empty string/list, it returns a default score.

    :param default_score: The score to return if input is missing or invalid.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            values1: Optional[Union[str, List[str]]],
            values2: Optional[Union[str, List[str]]]
        ) -> float:

            if tools.is_empty(values1) and tools.is_empty(values2):
                return 0.0
            elif tools.is_empty(values1) or tools.is_empty(values2):
                return default_score / 2

            # If inputs are valid, call the original function
            result = func(values1, values2)
            return result * (1 - default_score) + default_score

        return wrapper

    return decorator


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
@handle_missing_values()
def evaluate_editions(ed1, ed2):
    """Evaluate similarity of editions

    It uses a multilingual dictionary to fetch the edition number and
    compare it. Other textual elements are of less importance.

    :param ed1: string containing edition of the first record
    :param ed2: string containing edition of the second record

    :return: float with matching score
    """
    ed1_norm = score_editions.normalize_edition(ed1)
    ed2_norm = score_editions.normalize_edition(ed2)

    ed1_txt = ed1_norm.split(';')[-1]
    ed2_txt = ed2_norm.split(';')[-1]

    score_txt = tools.evaluate_text_similarity(ed1_txt, ed2_txt)

    score_numbers = score_editions.evaluate_norm_editions(ed1_norm, ed2_norm)

    if score_numbers != -1:
        return (score_txt + score_numbers * 9) / 10
    else:
        return score_txt





if __name__ == "__main__":
    pass