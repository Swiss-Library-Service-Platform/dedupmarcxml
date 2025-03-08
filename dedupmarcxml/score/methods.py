from typing import Dict
import numpy as np
import pandas as pd
from dedupmarcxml import tools

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
