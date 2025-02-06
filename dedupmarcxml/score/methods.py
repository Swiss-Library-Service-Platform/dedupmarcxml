from typing import Dict
import numpy as np

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
