"""
General tools to clean and normalize text
"""

import unicodedata
import re
from typing import Tuple, Optional, Callable, List, Dict, Union
import Levenshtein
import numpy as np
from lxml import etree
import pickle
import os
from functools import wraps
import itertools

editions_data = pickle.load(open(os.path.join(os.path.dirname(__file__), 'data/editions_data.pickle'), 'rb'))
publishers_data = pickle.load(open(os.path.join(os.path.dirname(__file__), 'data/publishers_data.pickle'), 'rb'))

def handle_values_lists(func: Callable) -> Callable:
    """
    Decorator to handle lists of values instead of single strings.
    It compares each value from the first list with each value from the second list
    and returns the maximum score found, with small penalty for each value not matched.
    """
    @wraps(func)
    def wrapper(values1: Union[List[str], str], values2: Union[List[str],str]) -> float:
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

            if is_empty(values1, key=key) and is_empty(values2, key=key):
                return 0.0
            elif is_empty(values1, key=key) or is_empty(values2, key=key):
                return default_score / 2

            # If inputs are valid, call the original function
            result = func(values1, values2)
            return result * (1 - default_score) + default_score

        return wrapper

    return decorator


def to_ascii(txt: str) -> str:
    """Transform txt to ascii, remove special chars, make upper case
    
    :param txt: string to normalize
    
    :return: string with normalized text
    """
    return unicodedata.normalize('NFKD', txt).upper().encode('ASCII', 'ignore').decode()


def remove_special_chars(txt: str, keep_dot: bool = False) -> str:
    """Remove special chars from txt

    :param txt: string to normalize
    :param keep_dot: boolean to keep dots

    :return: string with normalized text
    """

    # Remove special chars, we can make an exception for dots
    txt = re.sub(r'[^\w\s]' if keep_dot is False else r'[^\w\s\.]', ' ', txt)

    # remove duplicate spaces
    return re.sub(r'\s+', ' ', txt).strip()

def solve_abbreviations(txt1: str, txt2: str) -> Tuple[str, str]:
    """Solve abbreviations with dots

    If a txt contains "university" and the other "univ." the
    system will replace the "univ." with the complete form.

    :param txt1: string containing txt of the first record
    :param txt2: string containing txt of the second record

    :return: Tuple with the two updated txts
    """

    # If there are no dots, we can return the original txts
    if not('.' in txt1 or '.' in txt2):
        return txt1, txt2

    # Find the words that are only in one of the txts
    txt1_only_set = set(txt1.split()) - set(txt2.split())
    txt2_only_set = set(txt2.split()) - set(txt1.split())

    # Solve abbreviations
    # First for txt1
    for w1 in txt1_only_set:
        if w1.endswith('.') is False:
            continue
        substitutions = sorted([w2 for w2 in txt2_only_set if w2.startswith(w1[:-1])], key=len)
        if len(substitutions) > 0:
            txt1 = txt1.replace(w1, substitutions[-1])

    # Then for txt2
    for w2 in txt2_only_set:
        if w2.endswith('.') is False:
            continue
        substitutions = sorted([w1 for w1 in txt1_only_set if w1.startswith(w2[:-1])], key=len)
        if len(substitutions) > 0:
            txt2 = txt2.replace(w2, substitutions[-1])

    return txt1, txt2


def evaluate_text_similarity(txt1: str, txt2: str) -> float:
    """Evaluate similarity between two texts

    :param txt1: string containing text of the first record
    :param txt2: string containing text of the second record

    :return: float with matching score
    """

    if len(txt1) < len(txt2):
        txt1, txt2 = (txt2, txt1)

    t_list1 = re.findall(r'\b\w+\b', txt1)
    t_list2 = re.findall(r'\b\w+\b', txt2)
    if len(t_list1) < len(t_list2):
        t_list1, t_list2 = (t_list2, t_list1)

    diff = len(t_list1) - len(t_list2)
    coef = 1 / diff ** 0.05 - 0.15 if diff > 0 else 1

    score = 0
    # Idea is to compare the two texts word by word and take the best score.
    # If text 1 has 3 words and text 2 has 2 words: t1_w1 <=> t2_w1 / t1_w2 <=> t2_w2
    # Second test: t1_w2 <=> t2_w1 / t1_w3 <=> t2_w2
    # We use the max result between test 1 and 2
    for pos in range(len(t_list1) - len(t_list2) + 1):
        temp_score = np.mean([Levenshtein.ratio(t_list1[i + pos], t_list2[i]) for i in range(len(t_list2))])
        if temp_score > score:
            score = temp_score

    return coef * score


def roman_to_int(roman_number: str) -> Optional[int]:
    """roman_to_int(roman_number: str) -> Optional[int]
    Transform roman number to integer

    :param roman_number: roman number
    :return: int value of the number or None if the number is not valid
    """
    roman = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000, 'IV': 4, 'IX': 9, 'XL': 40, 'XC': 90,
             'CD': 400, 'CM': 900}
    i = 0
    num = 0
    max_val = 1000

    # Only capitals
    roman_number = roman_number.upper()

    while i < len(roman_number):
        # Check if a digramme like IV is in the number
        if i + 1 < len(roman_number) and roman_number[i:i + 2] in roman:
            new_val = roman[roman_number[i:i + 2]]
            if new_val > max_val:
                return None
            num += new_val
            max_val = roman[roman_number[i + 1]]
            i += 2

        elif roman_number[i] in roman:
            new_val = roman[roman_number[i]]
            if new_val > max_val:
                return None
            max_val = new_val
            num += new_val
            i += 1

    return num


def remove_ns(data: etree.Element) -> etree.Element:
    """Remove namespace from XML data
    :param data: `etree.Element` object with xml data
    :return: `etree.Element` without namespace information
    :rtype:
    """
    temp_data = etree.tostring(data).decode()
    temp_data = re.sub(r'\s?xmlns="[^"]+"', '', temp_data).encode()
    return etree.fromstring(temp_data)

def is_empty(value, key=None) -> bool:
    """Check if a value is None, an empty string, or an empty list."""

    if value is None:
        return True
    elif isinstance(value, str) and len(value.strip()) == 0:
        return True
    elif isinstance(value, list) and len(value) == 0:
        return True
    elif isinstance(value, dict) and key is not None and key not in value:
        return True
    elif isinstance(value, dict) and key is None and len(value) == 0:
        return True
    return False

def get_unique_combinations(l1: List[str], l2: List[str]) -> List[List[Tuple]]:
    """get_unique_combinations(l1: List[str], l2: List[str]) -> List[List[Tuple]]
    Used to search the best match with names like authors or publishers.

    :param l1: list of names to compare
    :param l2: list of names to compare

    :return: list of unique combinations of names
    """
    if len(l1) < len(l2):
        l2, l1 = (l1, l2)

    unique_combinations = []
    permutations = itertools.permutations(l1, len(l2))

    # zip() is called to pair each permutation
    # and shorter list element into combination
    for permutation in permutations:
        zipped = zip(permutation, l2)
        unique_combinations.append(list(zipped))
    return unique_combinations
