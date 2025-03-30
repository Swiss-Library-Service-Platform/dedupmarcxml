"""
Module for evaluating and processing publisher names for deduplication.

This module provides functions to normalize, solve abbreviations, correct small differences,
and evaluate the similarity between publisher names using vectorized systems.
"""

import re
import numpy as np
import Levenshtein
from typing import Tuple, Optional
from dedupmarcxml import tools


def normalize_publishers(pub1: str, pub2: str, keep_dash=True) -> Tuple[str, str, float]:
    """Normalize publisher names and calculate a factor to correct small differences

    This function normalizes the publisher names, solves abbreviations, and calculates a factor
    to correct small differences between the two names.

    :param pub1: string containing publisher of the first record
    :param pub2: string containing publisher of the second record
    :param keep_dash: boolean to keep dashes

    :return: tuple containing the two publisher names and a factor
        indicating to ponderate the final result in case of changes.
    """

    # Normalize publisher names
    pub1 = normalize_txt(pub1, keep_dot=True, keep_dash=keep_dash)
    pub2 = normalize_txt(pub2, keep_dot=True, keep_dash=keep_dash)

    # Solve abbreviations (with dots and in capitals)
    pub1, pub2 = tools.solve_abbreviations(pub1, pub2)

    # Dots are not needed anymore
    pub1 = re.sub(r'\.\s*', ' ', pub1)
    pub2 = re.sub(r'\.\s*', ' ', pub2)

    # Correct small differences
    pub1, pub2, factor = correct_small_differences(pub1, pub2)

    return pub1, pub2, factor

def normalize_txt(txt: str, keep_dot: Optional[bool] = False, keep_dash: Optional[bool] = False) -> str:
    """Transform txt to ascii, remove special chars, make upper case

    :param txt: string to normalize
    :param keep_dot: boolean to keep dots
    :param keep_dash: boolean to keep dashes

    :return: string with normalized text
    """

    # Clean dots of abbreviations
    txt_temp = re.sub(r'\b(\w)\.\s?\b', r'\1', txt)

    # Solve abbreviations specific to publishers
    for abbreviation, translation in tools.publishers_data['abbreviations'].items():
        if re.match(r'\b' + abbreviation + r'\b', txt_temp) is not None:
            txt_temp = re.sub(r'\b' + abbreviation + r'\b', translation, txt_temp)
            txt = txt_temp

    # Transform to ASCII and uppercase
    txt = tools.to_ascii(txt)

    # Remove unknown data
    txt = re.sub(r'EDITORE\sNON\sIDENTIFICATO|VERLAG\sNICHT\sERMITTELBAR|EDITEUR\sNON\sIDENTIFIE|PUBLISHER\sNOT\sIDENTIFIED',
            'PUBLISHER NOT IDENTIFIED', txt)

    return tools.remove_special_chars(txt, keep_dot=keep_dot, keep_dash=keep_dash)


def correct_small_differences(pub1: str, pub2: str) -> Tuple[str, str, float]:
    """Correct small differences between words of the publisher names

    If a correction is required, the factor value will be below 1 and reduce
    the final similarity score.

    :param pub1: string containing publisher of the first record
    :param pub2: string containing publisher of the second record

    :return: tuple containing the two publisher names and a factor
        indicating to ponderate the final result in case of changes.
    """

    # We use a log normalization to keep threshold between 0.8 (1 char difference) and
    # 0.92 at 20 chars in the word.
    get_threshold = lambda w_1, w_2: 0.8 + 0.12 * (np.log((len(w_1) + len(w_2)) / 2) / np.log(20))

    # We create set with the publishers, kind of bags of words
    pub1_set = set(pub1.split())
    pub2_set = set(pub2.split())

    # We get the not common words of each set
    # We need only to match words initially different
    pub1_only = list(pub1_set - pub2_set)
    pub2_only = list(pub2_set - pub1_set)

    # Initially factor is 1 and will be reduced in case of correction
    factor = 1

    # This variable is used to ponderate the reduction. If the publisher has a lot of words,
    # we reduce weight of corrections on the final score
    min_len = min([len(pub1_set), len(pub2_set)])

    # Iterate unique words of the first publisher to fetch
    # similar words in the other publisher
    for w1 in pub1_only:

        # We initiate best matching score and matched word
        best_w2 = None
        max_score = 0

        # Iterate words of the second publisher
        for w2 in pub2_only:
            score = Levenshtein.ratio(w1, w2)
            if score > get_threshold(w1, w2) and score > max_score:
                max_score = score
                best_w2 = w2

        # Once we finished to match words of the second publisher make the substitution if
        # we found a match
        if best_w2 is not None:

            # To decide the winner between the matching word of publisher 1 and the matching word of publisher 2,
            # we choose the most common.
            if tools.publishers_data['norm_counter'].get(best_w2, 1) < tools.publishers_data['norm_counter'].get(w1, 1):
                pub1 = re.sub(r'\b' + w1 + r'\b', best_w2, pub1)
            else:
                pub2 = re.sub(r'\b' + best_w2 + r'\b', w1, pub2)

            # Calculation of the factor. The penalty is reduced according to the number of words of the publishers
            factor = factor * 1 - ((1 - max_score) / min_len)

    # return pd.DataFrame(combs, columns=['pub1', 'pub2'])
    return pub1, pub2, factor


def evaluate_publishers_vect(pub1, pub2):
    """Calculate angle between the two publisher names.

    Angle is normalized between 1 and 0. Value of 1 indicates complete match. To calculate
    the angle we use the publishers data pickle: "publishers_data.pickle". Each word
    has value related to his frequency in the corpus.

    :param pub1: string containing publisher of the first record
    :param pub2: string containing publisher of the second record

    :return: float containing angle between the two vectors.
    """

    normalize_vectors = lambda x: x ** 4

    # Build bag of words
    pub1_set = set(pub1.split())
    pub2_set = set(pub2.split())

    # Create a list with union of the two sets. It is useful to build same
    # length vectors.
    pub_words = list(set.union(set(pub2.split()), set(pub1.split())))

    vect1 = []
    vect2 = []

    # Iterate the common list to build the two vectors
    for w in pub_words:

        # Build vector for publisher 1
        if w in pub1_set:

            # if the word is absent of the model, we assign max value: 1
            vect1.append(normalize_vectors(tools.publishers_data['norm_counter'].get(w, 1)))
        else:
            # if word is absent, vector value will be 0
            vect1.append(0)

        # Build vector for publisher 2
        if w in pub2_set:
            vect2.append(normalize_vectors(tools.publishers_data['norm_counter'].get(w, 1)))
        else:
            vect2.append(0)

    # transform to numpy array to be able to use numpy dot product
    vect1 = np.array(vect1)
    vect2 = np.array(vect2)

    # Calculate norms of the two vectors
    norm_vect1 = np.linalg.norm(vect1)
    norm_vect2 = np.linalg.norm(vect2)

    # Dot product of the two vectors
    dot_product = np.dot(vect1, vect2)

    # Normalization using the product of the norms
    if norm_vect1 * norm_vect2 == 0:
        return 0
    cos_theta = dot_product / (norm_vect1 * norm_vect2)

    # Be sure to have correct interval data
    cos_theta = np.clip(cos_theta, -1, 1)

    # Calculate angle
    angle = np.arccos(cos_theta)

    # Normalize angle value to have it between 0 and 1.
    return 1 - angle / np.pi * 2
