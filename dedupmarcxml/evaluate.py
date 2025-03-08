"""
Module to evaluate similarity between records

This module is the entry point to evaluate similarity between records. It uses
different submodules to evaluate different fields.
"""
# from dedupmarcxml.score. import score_publishers, score_editions, score_extent, score_names
from dedupmarcxml import score as scorelib
from dedupmarcxml import tools
from typing import List, Dict, Optional, Literal
from dedupmarcxml.briefrecord import BriefRec, BriefRecFactory
import numpy as np
from copy import deepcopy
import re


@tools.handle_missing_values(key='type')
def evaluate_format(format1: Dict, format2: Dict) -> float:
    """Evaluate similarity of formats

    This function evaluates the similarity of two formats. It penalizes
    records if they don't have 33X fields. If records with 33X fields are
    available, they will be preferred if other fields are similar.

    :param format1: dictionary containing format of the first record
    :param format2: dictionary containing format of the second record

    :return: float with matching score
    """

    score = 0

    # If the type is different, we don't need to go further
    if format1['type'] != format2['type']:
        return score

    # If the analytical is different, we don't need to go further, we cannot merge
    # analytical and non-analytical records
    if format1['analytical'] != format2['analytical']:
        return score

    # Access value is very important
    if format1['access'] == format2['access']:
        score += 0.55

    # Compare fields 33X => 0.45 max for the 3 fields
    f33x_1 = format1['f33x'].strip().split(';')
    f33x_2 = format2['f33x'].strip().split(';')
    for i in range(len(f33x_1)):
        if len(f33x_2) > i:
            if f33x_1[i] == f33x_2[i]:
                score += 0.15
            elif f33x_1[i].strip() == '' and f33x_2[i].strip() == '':
                score += 0.5
            elif f33x_1[i].strip() == '' or f33x_2[i].strip() == '':
                score += 0.1

    return score


@tools.handle_values_lists
@tools.handle_missing_values()
def evaluate_titles(title1: Dict,
                    title2: Dict) -> float:
    """Evaluate similarity of short titles

    :param title1: string containing short title of the first record
    :param title2: string containing short title of the second record

    :return: float with matching score
    """
    norm_title1 = tools.to_ascii(' '.join([title1['m'], title1['s']]))
    norm_title2 = tools.to_ascii(' '.join([title2['m'], title2['s']]))

    norm_title1 = tools.remove_special_chars(norm_title1)
    norm_title2 = tools.remove_special_chars(norm_title2)

    return tools.evaluate_text_similarity(norm_title1, norm_title2)


@tools.handle_values_lists
@tools.handle_missing_values(key='m')
def evaluate_short_titles(title1: str, title2: str) -> float:
    """Evaluate similarity of short titles

    :param title1: string containing short title of the first record
    :param title2: string containing short title of the second record

    :return: float with matching score
    """
    norm_title1 = tools.to_ascii(title1)
    norm_title2 = tools.to_ascii(title2)

    norm_title1 = tools.remove_special_chars(norm_title1)
    norm_title2 = tools.remove_special_chars(norm_title2)

    return tools.evaluate_text_similarity(norm_title1, norm_title2)


@tools.handle_missing_values()
def evaluate_creators(creators1: List[str], creators2: List[str]) -> float:
    """Evaluate similarity of creators

    :param creators1: list of creators of the first record
    :param creators2: list of creators of the second record

    :return: float with matching score
    """
    score = scorelib.names.evaluate_lists_names(creators1, creators2)

    return score


@tools.handle_missing_values()
def evaluate_languages(lang1: List[str], lang2: List[str]) -> float:
    """Evaluate similarity of languages

    :param lang1: list of languages of the first record
    :param lang2: list of languages of the second record

    :return: float with matching score
    """
    lang1 = ['und' if lang=='zxx' else lang for lang in lang1]
    lang2 = ['und' if lang=='zxx' else lang for lang in lang2]

    score = len(set.intersection(set(lang1), set(lang2))) / len(set.union(set(lang1), set(lang2)))
    if lang1[0] == lang2[0]:
        score = 0.7 + 0.3 * score

    if (lang1 + lang2).count('und') == 1:
        score = -0.1
    return score


@tools.handle_values_lists
@tools.handle_missing_values()
def evaluate_publishers(pub1: str, pub2: str) -> float:
    """Evaluate publishers using a vectorized system

    :param pub1: string containing publisher of the first record
    :param pub2: string containing publisher of the second record

    :return: float with matching score
    """

    # We normalize the publishers and calculate a factor
    pub1, pub2, factor = scorelib.publishers.normalize_publishers(pub1, pub2)

    # We calculate vectorized similarity
    score_vect = scorelib.publishers.evaluate_publishers_vect(pub1, pub2)

    # we correct the result with a factor granted by misspelling test
    return score_vect * factor


@tools.handle_values_lists
@tools.handle_missing_values(key='txt')
def evaluate_editions(ed1: Dict, ed2: Dict) -> float:
    """Evaluate similarity of editions

    It uses a multilingual dictionary to fetch the edition number and
    compare it. Other textual elements are of less importance.

    :param ed1: string containing edition of the first record
    :param ed2: string containing edition of the second record

    :return: float with matching score
    """

    score_txt = tools.evaluate_text_similarity(ed1['txt'], ed2['txt'])
    score_numbers = scorelib.editions.evaluate_norm_editions(ed1['nb'], ed2['nb'])

    if score_numbers != -1:
        return (score_txt + score_numbers * 9) / 10
    else:
        return score_txt


@tools.handle_missing_values(key='nb')
def evaluate_extent(extent1_dict: Dict, extent2_dict: Dict, rec_type: Optional[str] = None) -> float:
    """Evaluate similarity of extent

    Idea is to calculate three scores and combine them:
    - score1: extent comparison (strict)
    - score2: extent comparison (rounded)
    - score3: extent sum comparison

    :param extent1_dict: dictionary containing extent of the first record
    :param extent2_dict: dictionary containing extent of the second record
    :param rec_type: type of the record

    :return: float with matching score
    """

    extent1 = extent1_dict['nb']
    extent2 = extent2_dict['nb']

    extent_set1 = set(extent1)
    extent_set2 = set(extent2)
    score1 = scorelib.extent.calc_with_sets(extent_set1, extent_set2)

    rounded_extent1 = scorelib.extent.get_rounded_extent(extent_set1)
    rounded_extent2 = scorelib.extent.get_rounded_extent(extent_set2)
    score2 = scorelib.extent.calc_with_sets(rounded_extent1, rounded_extent2)

    score3 = scorelib.extent.calc_with_sum(extent1, extent2)

    # If sum is very different of other evaluation and very high we consider it as a good match. Maybe the librarians
    # added parts of the book in the extent.

    if score3 - score1 > 0.5 and score3 > 0.95 and sum(extent1) + sum(extent2) > 100:
        score = (score1 + score2 + score3 * 10) / 12
    else:
        score = (score1 + score2 + score3) / 3

    if rec_type == 'Notated music':
        score = scorelib.extent.calc_notated_music_score(extent1_dict['txt'], extent2_dict['txt'], score)

    return score


@tools.handle_values_lists
@tools.handle_missing_values()
def evaluate_years(year1: int, year2: int) -> float:
    """Evaluate similarity of years

    :param year1: integer containing year of the first record
    :param year2: integer containing year of the second record

    :return: float with matching score
    """
    return 1 / ((abs(year1 - year2) * .5) ** 2 + 1)


@tools.handle_missing_values(key='y1')
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


@tools.handle_missing_values()
def evaluate_parent(parent1: Dict, parent2: Dict) -> float:
    """evaluate_parents(parent1: Dict, parent2: Dict) -> float
    Evaluate similarity based on the link to the parent

    Keys of the parent dictionary:
    - title: title of the parent
    - std_num: content of $x or of $z
    - number: content of $g no:<content>
    - year: content of $g yr:<content> or first 4 digits numbers in a $g
    - parts: longest list of numbers in a $g

    :param parent1: dictionary with parent information
    :param parent2: dictionary with parent information

    :return: similarity score between two parents
    """

    score_title = 0
    score_identifiers = None
    score_year = None
    score_no = None
    score_parts = None

    if 'title' in parent1 and 'title' in parent2:
        score_title = tools.evaluate_text_similarity(parent1['title'], parent2['title'])

    if 'issn' in parent1 and 'issn' in parent2:
        score_identifiers = evaluate_identifiers([parent1['issn']], [parent2['issn']])
    elif 'isbn' in parent1 and 'isbn' in parent2:
        score_identifiers = evaluate_identifiers([parent1['isbn']], [parent2['isbn']])

    if 'number' in parent1 and 'number' in parent2:
        score_no = int(BriefRecFactory.normalize_extent(parent1['number']) ==
                       BriefRecFactory.normalize_extent(parent2['number']))

    if 'year' in parent1 and 'year' in parent2:
        score_year = int(parent1['year'] == parent2['year'])

    for p in [parent1, parent2]:

        # Create parts field if not present => used to compare two records with parts fields
        if 'parts' not in p:
            parts = []
            if 'number' in p:
                parts += BriefRecFactory.normalize_extent(p['number'])
            if 'year' in p:
                parts.append(p['year'])
            if len(parts) > 0:
                p['parts'] = parts

    parent1 = deepcopy(parent1)
    parent2 = deepcopy(parent2)
    if 'parts' in parent1 and 'parts' in parent2 and 'nb' in parent1['parts'] and 'nb' in parent2['parts']:
        initial_nb = sum([len(parent1['parts']['nb']), len(parent2['parts']['nb'])])
        to_delete = []
        for e in parent1['parts']['nb']:
            if e in parent2['parts']['nb']:
                to_delete.append(e)
                parent2['parts']['nb'].remove(e)
        for e in to_delete:
            parent1['parts']['nb'].remove(e)

        to_delete = []
        for e in parent2['parts']['nb']:
            if e in parent1['parts']['nb']:
                to_delete.append(e)
                parent1['parts']['nb'].remove(e)
        for e in to_delete:
            parent2['parts']['nb'].remove(e)

        final_nb = sum([len(parent1['parts']['nb']), len(parent2['parts']['nb'])])
        score_parts = 1 - final_nb / initial_nb

    elif 'parts' in parent1 or 'parts' in parent2:
        # Case if part information is only in one record available
        score_parts = 0

    return score_title * np.mean([s for s in [score_title, score_no, score_year, score_identifiers, score_parts]
                                  if s is not None])


@tools.handle_missing_values()
def evaluate_std_nums(ids1: List[str], ids2: List[str]) -> float:
    """Return the result of the evaluation of similarity of two lists of identifiers.

    :param ids1: list of identifiers to compare
    :param ids2: list of identifiers to compare

    :return: similarity score between two lists of identifiers as float
    """
    ids1 = set(ids1)
    ids2 = set(ids2)

    if len(set.union(ids1, ids2)) > 0:
        score1 = len(set.intersection(ids1, ids2)) / len(set.union(ids1, ids2))
        score1 = score1 ** .05 if score1 > 0 else 0
    else:
        score1 = 0

    for num in deepcopy(ids1):
        num_digit = re.sub(r'\D', '', num)
        if len(num_digit) > 0:
            ids1.add(num_digit)

    for num in deepcopy(ids2):
        num_digit = re.sub(r'\D', '', num)
        if len(num_digit) > 0:
            ids2.add(num_digit)

    if len(set.union(ids1, ids2)) > 0:
        score2 = len(set.intersection(ids1, ids2)) / len(set.union(ids1, ids2))
        score2 = score2 ** .05 if score2 > 0 else 0
    else:
        score2 = 0
    if score1 > score2:
        return score1
    else:
        return score2 * 0.9

@tools.handle_missing_values()
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



def evaluate_records_similarity(rec1: BriefRec, rec2: BriefRec) -> Dict[str, float]:
    """Evaluate similarity between two records

    :param rec1: BriefRecord object
    :param rec2: BriefRecord object

    :return: float with matching score
    """
    # We need to know the record type to calculate the similarity of extent
    if rec1.data['format']['type'] == rec2.data['format']['type']:
        rec_type = rec1.data['format']['type']
    else:
        rec_type = None

    # We evaluate the similarity of the formats
    score_format = evaluate_format(rec1.data['format'], rec2.data['format'])

    # We evaluate the similarity of the titles
    score_title = evaluate_titles(rec1.data['titles'], rec2.data['titles'])

    # We evaluate the similarity of the short titles
    score_short_title = evaluate_short_titles(rec1.data['short_titles'], rec2.data['short_titles'])

    # We evaluate the similarity of the creators
    score_creators = evaluate_creators(rec1.data['creators'], rec2.data['creators'])

    # We evaluate the similarity of the corporate creators
    score_corp_creators = evaluate_creators(rec1.data['corp_creators'], rec2.data['corp_creators'])

    # We evaluate the similarity of the languages
    score_lang = evaluate_languages(rec1.data['languages'], rec2.data['languages'])

    # We evaluate the similarity of the publishers
    score_pub = evaluate_publishers(rec1.data['publishers'], rec2.data['publishers'])

    # We evaluate the similarity of the editions
    score_ed = evaluate_editions(rec1.data['editions'], rec2.data['editions'])

    # We evaluate the similarity of the extent
    score_ext = evaluate_extent(rec1.data['extent'], rec2.data['extent'], rec_type=rec_type)

    # We evaluate the similarity of the years
    score_yr = evaluate_years_start_and_end(rec1.data['years'], rec2.data['years'])

    # We evaluate the similarity of the series
    score_series = evaluate_short_titles(rec1.data['series'], rec2.data['series'])

    # We evaluate the similarity of the parent
    score_parent = evaluate_parent(rec1.data['parent'], rec2.data['parent'])

    # We evaluate the similarity of the standard numbers
    score_std_nums = evaluate_std_nums(rec1.data['std_nums'], rec2.data['std_nums'])

    # We evaluate the similarity of system numbers
    score_sys_nums = evaluate_identifiers(rec1.data['sys_nums'], rec2.data['sys_nums'])

    return {'format': score_format,
            'titles': score_title,
            'short_titles': score_short_title,
            'creators': score_creators,
            'corp_creators': score_corp_creators,
            'languages': score_lang,
            'publishers': score_pub,
            'editions': score_ed,
            'extent': score_ext,
            'years': score_yr,
            'series': score_series,
            'parent': score_parent,
            'std_nums': score_std_nums,
            'sys_nums': score_sys_nums}


def get_similarity_score(sim_analysis: Dict[str, float],
                         method: Optional[str] = 'mean') -> float:
    """Return the similarity score between two records

    It uses the result of the evaluation of similarity of two records
    (func:`dedupmarcxml.evaluate.evaluate_records_similarity`).

    :param sim_analysis: dictionary containing the results of the evaluation of similarity of two records
    :param method: method to use to calculate the similarity score, default method is the mean

    :return: similarity score between two records as float
    """
    if method == 'random_forest_music':
        return scorelib.methods.random_forest_music(sim_analysis)
    return scorelib.methods.mean(sim_analysis)


if __name__ == "__main__":
    pass
