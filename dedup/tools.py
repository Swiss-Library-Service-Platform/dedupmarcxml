"""
General tools to clean and normalize text
"""

import unicodedata
import re
from typing import Tuple, Optional
import Levenshtein
import numpy as np
from lxml import etree
import pickle
import os

editions_data = pickle.load(open(os.path.join(os.path.dirname(__file__), 'data/editions_data.pickle'), 'rb'))

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
    elif isinstance(value, dict) and key not in value:
        return True
    return False