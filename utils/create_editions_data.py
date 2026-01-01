"""
This script generates a pickled data file containing a mapping of edition number expressions
(in various languages and forms) to their corresponding numeric values. The resulting file,
`editions_data.pickle`, is intended to be used as a reference for analyzing and extracting
edition numbers from text data.

The script normalizes and processes a multilingual dictionary of cardinal and ordinal number
expressions, removes digit-based variants, and stores the cleaned mapping in an
OrderedDict sorted by expression length (descending). The output file is saved to
`dedupmarcxml/data/editions_data.pickle` for use in edition number extraction tasks.
"""


# import libraries
import os
from collections import OrderedDict
import re
import pickle
import unicodedata

numbers_dict = {
    "fr": {
        "cardinal": {
            1: ["un", "une"], 2: ["deux"], 3: ["trois"], 4: ["quatre"], 5: ["cinq"],
            6: ["six"], 7: ["sept"], 8: ["huit"], 9: ["neuf"], 10: ["dix"],
            11: ["onze"], 12: ["douze"], 13: ["treize"], 14: ["quatorze"], 15: ["quinze"],
            16: ["seize"], 17: ["dix-sept"], 18: ["dix-huit"], 19: ["dix-neuf"], 20: ["vingt"]
        },
        "ordinal": {
            1: ["premier", "1er", "1re", "première", "1ère"], 2: ["second", "2e", "sec.", "seconde", "2nd", "deuxième"], 3: ["troisième", "3e", "3rd"],
            4: ["quatrième", "4e", "quatr.", "4th"], 5: ["cinquième", "5e", "5th"], 6: ["sixième", "6e", "6th"],
            7: ["septième", "7e", "7th"], 8: ["huitième", "8e", "8th"], 9: ["neuvième", "9e", "9th"],
            10: ["dixième", "10e", "10th"], 11: ["onzième", "11e", "11th"], 12: ["douzième", "12e", "12th"],
            13: ["treizième", "13e", "13th"], 14: ["quatorzième", "14e", "14th"], 15: ["quinzième", "15e", "15th"],
            16: ["seizième", "16e", "16th"], 17: ["dix-septième", "17e", "17th"], 18: ["dix-huitième", "18e", "18th"],
            19: ["dix-neuvième", "19e", "19th"], 20: ["vingtième", "20e", "20th"]
        }
    },
    "en": {
        "cardinal": {
            1: ["one"], 2: ["two"], 3: ["three"], 4: ["four"], 5: ["five"],
            6: ["six"], 7: ["seven"], 8: ["eight"], 9: ["nine"], 10: ["ten"],
            11: ["eleven"], 12: ["twelve"], 13: ["thirteen"], 14: ["fourteen"], 15: ["fifteen"],
            16: ["sixteen"], 17: ["seventeen"], 18: ["eighteen"], 19: ["nineteen"], 20: ["twenty"]
        },
        "ordinal": {
            1: ["first", "1st", "1st."], 2: ["second", "2nd", "sec.", "2nd."], 3: ["third", "3rd", "3rd."],
            4: ["fourth", "4th", "4th."], 5: ["fifth", "5th", "5th."], 6: ["sixth", "6th", "6th."],
            7: ["seventh", "7th", "7th."], 8: ["eighth", "8th", "8th."], 9: ["ninth", "9th", "9th."],
            10: ["tenth", "10th", "10th."], 11: ["eleventh", "11th", "11th."], 12: ["twelfth", "12th", "12th."],
            13: ["thirteenth", "13th", "13th."], 14: ["fourteenth", "14th", "14th."], 15: ["fifteenth", "15th", "15th."],
            16: ["sixteenth", "16th", "16th."], 17: ["seventeenth", "17th", "17th."], 18: ["eighteenth", "18th", "18th."],
            19: ["nineteenth", "19th", "19th."], 20: ["twentieth", "20th", "20th."]
        }
    },
    "es": {
        "cardinal": {
            1: ["uno", "una"], 2: ["dos"], 3: ["tres"], 4: ["cuatro"], 5: ["cinco"],
            6: ["seis"], 7: ["siete"], 8: ["ocho"], 9: ["nueve"], 10: ["diez"],
            11: ["once"], 12: ["doce"], 13: ["trece"], 14: ["catorce"], 15: ["quince"],
            16: ["dieciséis"], 17: ["diecisiete"], 18: ["dieciocho"], 19: ["diecinueve"], 20: ["veinte"]
        },
        "ordinal": {
            1: ["primero", "1°", "primera", "1ra"], 2: ["segundo", "2°", "sec.", "segunda", "2da"], 3: ["tercero", "3°", "3ra"],
            4: ["cuarto", "4°", "cuatr."], 5: ["quinto", "5°", "5to"], 6: ["sexto", "6°", "6to"],
            7: ["séptimo", "7°", "7mo"], 8: ["octavo", "8°", "8vo"], 9: ["noveno", "9°", "9no"],
            10: ["décimo", "10°", "10mo"], 11: ["undécimo", "11°", "11mo"], 12: ["duodécimo", "12°", "12mo"],
            13: ["decimotercero", "13°", "13ro"], 14: ["decimocuarto", "14°", "14to"], 15: ["decimoquinto", "15°", "15to"],
            16: ["decimosexto", "16°", "16to"], 17: ["decimoséptimo", "17°", "17mo"], 18: ["decimoctavo", "18°", "18vo"],
            19: ["decimonoveno", "19°", "19no"], 20: ["vigésimo", "20°", "20mo"]
        }
    },
    "it": {
        "cardinal": {
            1: ["uno", "una"], 2: ["due"], 3: ["tre"], 4: ["quattro"], 5: ["cinque"],
            6: ["sei"], 7: ["sette"], 8: ["otto"], 9: ["nove"], 10: ["dieci"],
            11: ["undici"], 12: ["dodici"], 13: ["tredici"], 14: ["quattordici"], 15: ["quindici"],
            16: ["sedici"], 17: ["diciassette"], 18: ["diciotto"], 19: ["diciannove"], 20: ["venti"]
        },
        "ordinal": {
            1: ["primo", "1°", "prima", "1ra"], 2: ["secondo", "2°", "sec.", "seconda", "2da"], 3: ["terzo", "3°", "3ra"],
            4: ["quarto", "4°", "quart."], 5: ["quinto", "5°", "5to"], 6: ["sesto", "6°", "6to"],
            7: ["settimo", "7°", "7mo"], 8: ["ottavo", "8°", "8vo"], 9: ["nono", "9°", "9no"],
            10: ["decimo", "10°", "10mo"], 11: ["undicesimo", "11°", "11mo"], 12: ["dodicesimo", "12°", "12mo"],
            13: ["tredicesimo", "13°", "13ro"], 14: ["quattordicesimo", "14°", "14to"], 15: ["quindicesimo", "15°", "15to"],
            16: ["sedicesimo", "16°", "16to"], 17: ["diciassettesimo", "17°", "17mo"], 18: ["diciottesimo", "18°", "18vo"],
            19: ["diciannovesimo", "19°", "19no"], 20: ["ventesimo", "20°", "20mo"]
        }
    },
    "de": {
        "cardinal": {
            1: ["eins"], 2: ["zwei"], 3: ["drei"], 4: ["vier"], 5: ["fünf"],
            6: ["sechs"], 7: ["sieben"], 8: ["acht"], 9: ["neun"], 10: ["zehn"],
            11: ["elf"], 12: ["zwölf"], 13: ["dreizehn"], 14: ["vierzehn"], 15: ["fünfzehn"],
            16: ["sechzehn"], 17: ["siebzehn"], 18: ["achtzehn"], 19: ["neunzehn"], 20: ["zwanzig"]
        },
        "ordinal": {
            1: ["erste", "erstausgabe", "1."], 2: ["zweite", "zweitausgabe", "2.", "sec."], 3: ["dritte", "3."],
            4: ["vierte", "4.", "vort."], 5: ["fünfte", "5."], 6: ["sechste", "6."],
            7: ["siebte", "7."], 8: ["achte", "8."], 9: ["neunte", "9."],
            10: ["zehnte", "10."], 11: ["elfte", "11."], 12: ["zwölfte", "12."]
        }
    },
    "nl": {
        "cardinal": {
            1: ["één"], 2: ["twee"], 3: ["drie"], 4: ["vier"], 5: ["vijf"],
            6: ["zes"], 7: ["zeven"], 8: ["acht"], 9: ["negen"], 10: ["tien"],
            11: ["elf"], 12: ["twaalf"], 13: ["dertien"], 14: ["veertien"], 15: ["vijftien"],
            16: ["zestien"], 17: ["zeventien"], 18: ["achttien"], 19: ["negentien"], 20: ["twintig"]
        },
        "ordinal": {
            1: ["eerste", "1e"], 2: ["tweede", "2e", "sec."], 3: ["derde", "3e"],
            4: ["vierde", "4e"], 5: ["vijfde", "5e"], 6: ["zesde", "6e"],
            7: ["zevende", "7e"], 8: ["achtste", "8e"], 9: ["negende", "9e"],
            10: ["tiende", "10e"], 11: ["elfde", "11e"], 12: ["twaalfde", "12e"],
            13: ["dertigste", "13e"], 14: ["veertiende", "14e"], 15: ["vijftiende", "15e"],
            16: ["zestiende", "16e"], 17: ["zeventiende", "17e"], 18: ["achttiende", "18e"],
            19: ["negentiende", "19e"], 20: ["twintigste", "20e"]
        }
    },
    "pt": {
        "cardinal": {
            1: ["um", "uma"], 2: ["dois", "duas"], 3: ["três"], 4: ["quatro"], 5: ["cinco"],
            6: ["seis"], 7: ["sete"], 8: ["oito"], 9: ["nove"], 10: ["dez"],
            11: ["onze"], 12: ["doze"], 13: ["treze"], 14: ["quatorze"], 15: ["quinze"],
            16: ["dezesseis"], 17: ["dezessete"], 18: ["dezoito"], 19: ["dezenove"], 20: ["vinte"]
        },
        "ordinal": {
            1: ["primeiro", "1º", "primeira"], 2: ["segundo", "2º", "sec.", "segunda"], 3: ["terceiro", "3º"],
            4: ["quarto", "4º"], 5: ["quinto", "5º"], 6: ["sexto", "6º"],
            7: ["sétimo", "7º"], 8: ["oitavo", "8º"], 9: ["nono", "9º"],
            10: ["décimo", "10º"], 11: ["décimo primeiro", "11º"], 12: ["décimo segundo", "12º"],
            13: ["décimo terceiro", "13º"], 14: ["décimo quarto", "14º"], 15: ["décimo quinto", "15º"],
            16: ["décimo sexto", "16º"], 17: ["décimo sétimo", "17º"], 18: ["décimo oitavo", "18º"],
            19: ["décimo nono", "19º"], 20: ["vigésimo", "20º"]
        }
    },
    "ro": {
        "ordinal": {
            1: ["I."], 2: ["II."], 3: ["III."],
            4: ["IV."], 5: ["V."], 6: ["VI."],
            7: ["VII."], 8: ["VIII."], 9: ["IX."],
            10: ["X."], 11: ["XI."], 12: ["XII."]
        }
    }
}

if __name__ == '__main__':
    d_numbers = OrderedDict()
    for lang in numbers_dict:
        for cat in numbers_dict[lang]:
            for nb in numbers_dict[lang][cat]:
                for v in numbers_dict[lang][cat][nb]:
                    if re.match(r'\d', v):
                        continue
                    txt = unicodedata.normalize('NFKD', v).upper().encode('ASCII', 'ignore').decode()
                    txt = re.sub(r'[^\w\s\.]', ' ', txt)
                    txt = re.sub(r'\s+', ' ', txt).strip()
                    d_numbers[txt] = nb

    d_numbers = OrderedDict(sorted(d_numbers.items(), key=lambda item: -len(item[0])))

    data_dir = os.path.join(os.path.dirname(__file__), '..', 'dedupmarcxml', 'data')
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, 'editions_data.pickle')

    with open('editions_data.pickle' ,'wb') as f:
        pickle.dump(d_numbers, f)
