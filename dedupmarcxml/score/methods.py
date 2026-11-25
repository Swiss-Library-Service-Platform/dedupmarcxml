from typing import Dict
import numpy as np
import pandas as pd
from dedupmarcxml import tools

method_list = ['mean', 'random_forest_book', 'random_forest_book_old' ,'random_forest_music', 'random_forest_general', 'random_forest_general_old']
columns = [
    'format', 'titles', 'short_titles', 'creators', 'corp_creators',
    'languages', 'publishers', 'editions', 'extent', 'years',
    'series', 'parent', 'std_nums', 'sys_nums',
]

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
        df = pd.DataFrame([results], columns=columns)
        score = tools.rf_general_model.predict_proba(df)[0][1]
    except ValueError:
        score = 0.0

    return score

def random_forest_book_old(results: Dict[str, float]) -> float:
    try:
        df = pd.DataFrame([results], columns=columns)
        score = tools.rf_book_model_old.predict_proba(df)[0][1]
    except ValueError:
        score = 0.0

    return score

def random_forest_general_old(results: Dict[str, float]) -> float:
    try:
        df = pd.DataFrame([results], columns=columns)
        score = tools.rf_general_model_old.predict_proba(df)[0][1]
    except ValueError:
        score = 0.0

    return score