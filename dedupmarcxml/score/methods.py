from typing import Dict
import numpy as np
import pandas as pd
from dedupmarcxml import tools

method_list = ['mean', 'random_forest_book', 'random_forest_music', 'mlp_book']

def mean(results: Dict[str, float]) -> float:
    """
    Calculate the mean of the values in the two dictionaries. We exclude
    missing values (0.0 and 0.1) from the calculation.

    :param results: dictionary with results values

    :return: mean of the values
    """
    norm_values = []

    for k, v in results.items():
        if v >= 0.2:
            norm_values.append(v)

    return np.mean(norm_values) if len(norm_values) > 0 else 0.0

def random_forest_music(results: Dict[str, float]) -> float:
    """
    Calculate the mean of the values in the two dictionaries. We exclude
    missing values (0.0 and 0.1) from the calculation.

    :param results: dictionary with results values

    :return: mean of the values
    """

    score = tools.rf_music_model.predict_proba(pd.DataFrame(results, index=[1]))[0][1]

    return score


def mlp_book(results: Dict[str, float]) -> float:
    """
    Calculate the probability according to the model using the
    values in the two dictionaries.

    :param results: dictionary with results values

    :return: calculated score of the classifier
    """
    try:
        score = tools.mlp_book_model.predict_proba(pd.DataFrame(results, index=[1]))[0][1]
    except ValueError:
        score = 0.0

    return score

def random_forest_book(results: Dict[str, float]) -> float:
    """
    Calculate the probability according to the model using the
    values in the two dictionaries.

    :param results: dictionary with results values

    :return: calculated score of the classifier
    """
    try:
        score = tools.rf_book_model.predict_proba(pd.DataFrame(results, index=[1]))[0][1]
    except ValueError:
        score = 0.0

    return score

def random_forest_general(results: Dict[str, float]) -> float:
    """
    Calculate the probability according to the model using the
    values in the two dictionaries.

    :param results: dictionary with results values

    :return: calculated score of the classifier
    """
    try:
        score = tools.rf_general_model.predict_proba(pd.DataFrame(results, index=[1]))[0][1]
    except ValueError:
        score = 0.0

    return score
