from lxml import etree
from typing import List, Optional, Dict, Union
import re
import logging
import json
from dedupmarcxml import tools
from abc import ABC, abstractmethod


class BriefRec(ABC):
    """Class representing a brief record object

    You can create a brief record object from a :class:`SruRecord` object or
    from the XML data of a MARCXML record using an Etree Element object.

    The namespaces are removed from the XML data.

    :ivar error: boolean, is True in case of error
    :ivar error_messages: list of string with the error messages
    :ivar data: json object with brief record information
    """

    def __init__(self) -> None:
        """Brief record object
        """
        self.error = False
        self.error_messages = []
        self.data = None

    def __str__(self) -> str:
        if self.data is not None:
            return json.dumps(self.data, indent=4)
        else:
            return ''

    def __repr__(self) -> str:
        if self.data is not None:
            return f"{self.__class__.__name__}(<'{self.data['rec_id']}'>)"
        else:
            return f"{self.__class__.__name__}(<No ID available>)"

    def __hash__(self) -> int:
        return hash(self.data['rec_id'])

    def __eq__(self, other) -> bool:
        return self.data['rec_id'] == other.data['rec_id']

    @abstractmethod
    def _get_bib_info(self) -> Dict:
        pass


class XmlBriefRec(BriefRec):
    def __init__(self, rec: etree.Element) -> None:
        """Brief record object

        :param rec: XML data of the record or :class:`SruRecord` object
        """
        super().__init__()

        if rec.__class__.__name__ == '_Element':
            self.src_data = tools.remove_ns(rec)
            self.data = self._get_bib_info()
        else:
            self.error = True
            self.error_messages.append(f'Wrong type of data provided: {type(rec)}')
            logging.error(f'BriefRec: wrong type of data provided: {type(rec)}')

    def _get_bib_info(self):
        return XmlBriefRecFactory.get_bib_info(self.src_data)


class JsonBriefRec(BriefRec):
    def __init__(self, rec: Dict) -> None:
        """Brief record object

        :param rec: XML data of the record or :class:`SruRecord` object
        """
        super().__init__()

        if rec.__class__.__name__ == 'dict':
            self.src_data = rec
            self.data = self._get_bib_info()
        else:
            self.error = True
            self.error_messages.append(f'Wrong type of data provided: {type(rec)}')
            logging.error(f'BriefRec: wrong type of data provided: {type(rec)}')

    def _get_bib_info(self):
        return JsonBriefRecFactory.get_bib_info(self.src_data)


class BriefRecFactory(ABC):
    """Class to create a brief record from a Marc21 record

    The class can parse several fields of the Marc21 record.

    :cvar bib_type: :class:`etree.Element` or :class:`Dict`
    """

    bib_type = Union[etree.Element, Dict]

    @classmethod
    @abstractmethod
    def find(cls, bib: bib_type, path:str) -> Optional[Union[str,List[Dict]]]:
        """Find a value in the MARCXML record

        :param bib: Marc21 record
        :param path: path to the value to find

        :return: value found or None if not found
        """
        pass

    @classmethod
    @abstractmethod
    def findall(cls, bib: bib_type, path:str) -> List[Union[str, List[Dict[str,str]]]]:
        """Find a value in the MARCXML record

        :param bib: Marc21 record
        :param path: path to the value to find

        :return: value found or None if not found
        """
        pass

    @classmethod
    def normalize_title(cls, title: str) -> str:
        """normalize_title(title: str) -> str
        Normalize title string

        Idea is to remove "<<" and ">>" of the title and remove
        all non-alphanumeric characters.

        :param title: title to normalize

        :return: string with normalized title
        """
        title = title.replace('<<', '').replace('>>', '')
        return title

    @classmethod
    def normalize_extent(cls, extent: str) -> Optional[Dict]:
        """Normalize extent string and return a dictionary with numbers

        :param extent: extent to normalize

        :return: a dictionary with keys 'nb' and 'txt'
        """
        extent_lower = extent.lower()
        extent_list = [int(f) for f in re.findall(r'\d+', extent_lower)]
        extent_list += [tools.roman_to_int(f) for f in re.findall(r'\b[ivxlcdm]+\b', extent_lower)
                        if tools.roman_to_int(f) is not None]

        return {'nb': sorted(extent_list, reverse=True), 'txt': extent}

    @classmethod
    def normalize_isbn(cls, isbn: str) -> Optional[str]:
        """Suppress hyphen and textual information of the provided isbn

        :param isbn: raw string containing isbn

        :return: string containing normalized isbn
        """
        # Remove hyphens and all textual information about isbn
        m = re.search(r'\d{8,}[\dxX]', isbn.replace('-', ''))
        if m is not None:
            return m.group()

    @classmethod
    def normalize_issn(cls, issn: str) -> Optional[str]:
        """Suppress hyphen and textual information of the provided issn

        :param issn: raw string containing issn

        :return: string containing normalized issn
        """
        # Remove hyphens and all textual information about isbn
        m = re.search(r'\d{7}[\dxX]', issn.replace('-', ''))
        if m is not None:
            return m.group()

    @classmethod
    def extract_year(cls, txt: str) -> Optional[int]:
        """extract_year(str) -> Optional[int]
        Extract a substring of 4 digits

        :param txt: string to parse to get year

        :return: int value with the found year or None if no year available
        """
        m = re.search(r'\b\d{4}\b', txt)
        if m is not None:
            return int(m.group())

    @classmethod
    def get_rec_id(cls, bib: bib_type) -> Optional[str]:
        """
        Get the record ID

        :param bib: :class:`etree.Element`

        :return: record ID or None if not found
        """
        return cls.find(bib, '001')

    @classmethod
    def get_std_num(cls, bib: bib_type) -> Optional[List[str]]:
        """
        Get a list of standardized numbers like DOI

        :param bib: :class:`etree.Element`

        :return: set of standardized numbers
        """

        # Get isbn fields
        raw_isbns = set(cls.findall(bib, '020$$a'))
        isbns = set()

        for raw_isbn in raw_isbns:
            isbn = cls.normalize_isbn(raw_isbn)
            if isbn is not None:
                isbns.add(isbn)

        # Get ISSN fields
        raw_issns = set(cls.findall(bib, '022$$a'))
        issns = set()

        for raw_issn in raw_issns:
            issn = cls.normalize_issn(raw_issn)
            if issn is not None:
                issns.add(issn)

        # Get other standardized numbers
        std_nums = set(cls.findall(bib, '024$$a'))

        # Get other publisher numbers
        pub_nums = set(cls.findall(bib, '028$$a'))

        if len(isbns) == 0 and len(issns) == 0 and len(std_nums) == 0 and pub_nums == 0:
            return None

        return list(set.union(isbns, issns, std_nums, pub_nums))

    @classmethod
    def get_leader_pos67(cls, bib: bib_type) -> Optional[str]:
        """
        Get the leader position 6 and 7

        Used to determine the format of the record

        :param bib: :class:`etree.Element`

        :return: leader position 6 and 7 or None if not found
        """

        leader = cls.find(bib, 'leader')
        if leader is not None:
            return leader[6:8]

    @classmethod
    def get_sys_nums(cls, bib: bib_type) -> Optional[List[str]]:
        """
        Get a set of system numbers

        :param bib: :class:`etree.Element`

        :return: set of system numbers
        """
        sys_nums = set(cls.findall(bib, '035$$a'))

        if len(sys_nums) == 0:
            return None

        return list(sys_nums)

    @classmethod
    def get_titles(cls, bib: bib_type) -> List[Dict]:
        """
        Get all titles of the record.

        This function retrieves the titles from the 245 and 246 fields of a MARC record. The
        function returns a list of dictionaries with keys 'm' and 's' for the main and
        subtitle of the title.

        :param bib: :class:`etree.Element`

        :return: List of titles of the record.
        """
        titles = []
        for tag in ['245', '246']:
            fields = cls.findall(bib, tag)
            for field in fields:
                title = dict()

                subfield_a = ''
                subfields_bp = []
                for subfield in field:
                    if 'a' in subfield:
                        subfield_a = subfield['a']
                    elif 'b' in subfield:
                        subfields_bp.append(subfield['b'])
                    elif 'p' in subfield:
                        subfields_bp.append(subfield['p'])

                title['m'] = cls.normalize_title(subfield_a)

                title['s'] = ': '.join(subfields_bp) if len(subfields_bp) > 0 else ''

                titles.append(title)

        return titles


    @classmethod
    def get_years(cls, bib: bib_type) -> Optional[Dict]:
        """Get the dates of publication from 008 and 264$$c fields

        This function retrieves the publication years from the 008 control
        field and the 264$c data field of a MARC record. 264c is only used when
        different of 008.

        :param bib: :class:`etree.Element`

        :return: dictionary with keys 'year1' and optionally 'year2', or None if no year is found
        """
        controlfield008 = cls.find(bib, '008')
        field_264c = cls.find(bib, '264$$c')

        year1 = []
        year2 = None

        # Check source 1: 008
        if controlfield008 is not None:
            year1_008 = cls.extract_year(controlfield008[7:11])
            if year1_008 is not None:
                year1.append(year1_008)
            year2_008 = cls.extract_year(controlfield008[11:15])
            if year2_008 is not None:
                year2 = year2_008

        # Check source 2: 264$$c
        if field_264c is not None:
            year1_264c = cls.extract_year(field_264c)

            if year1_264c is not None and year1_264c not in year1:
                year1.append(year1_264c)

        # Build dictionary to return the data. We don't use year2 key if
        # not available.
        if len(year1) == 0:
            return None
        elif year2 is not None:
            return {'y1': year1, 'y2': year2}
        else:
            return {'y1': year1}

    @classmethod
    def get_33x_summary(cls, bib: bib_type) -> Optional[str]:
        """ get_33x_summary(bib: etree.Element) -> Optional[str]
        Get a summary of the 336, 337 and 338 fields

        :param bib: :class:`etree.Element`

        :return: summary of the 336, 337 and 338 fields"""
        s = ''
        for tag in ['336', '337', '338']:
            fields = cls.findall(bib, f'{tag}$$b')
            if len(fields) > 0:
                s += ','.join(fields) + ';'
            else:
                s += ' ;'
        s = s[:-1]  # remove last ; character
        return s

    @classmethod
    def get_bib_resource_type(cls, bib: bib_type) -> str:
        """Get the resource type of the record

        The analyse is mainly based on the leader position 6 and 7.
        To distinguish between series and journal, we use the field
        008 pos. 6.

        :param bib: :class:`etree.Element`

        :return: resource type of the record
        """

        pos6, pos7 = cls.get_leader_pos67(bib)
        if pos6 in 'a':
            if pos7 in 'acdm':
                return 'Book'
            elif pos7 in 'bis':
                if cls.find(bib, '008')[21] in 'pn':
                    return 'Journal'
                else:
                    return 'Series'

        elif pos6 in 'c':
            return 'Notated Music'

        elif pos6 in 'ij':
            return 'Audio'

        elif pos6 in 'ef':
            return 'Map'

        elif pos6 in 'dt':
            return 'Manuscript'

        elif pos6 in 'ef':
            return 'Map'

        elif pos6 in 'k':
            return 'Image'

        elif pos6 in 'ro':
            return 'Object'

        elif pos6 in 'g':
            return 'Video'

        elif pos6 in 'p':
            return 'Mixed Material'

        return 'Book'

    @classmethod
    def get_access_type(cls, bib: bib_type) -> Optional[str]:
        """get_access_type(bib: etree.Element) -> Optional[str]
        Get the access type of the record

        :param bib: :class:`etree.Element`

        :return: access type of the record
        """
        if cls.is_micro(bib) is True:
            return 'Microform'
        if cls.is_online(bib) is True:
            return 'Online'
        if cls.is_braille(bib) is True:
            return 'Braille'

        return 'Physical'

    @classmethod
    def get_format(cls, bib: bib_type) -> Dict:
        """get_format(bib: etree.Element) -> Optional[str]
        Get the format of the record from leader field position 6 and 7

        :param bib: :class:`etree.Element`

        :return: format of the record
        """
        res_format = {'type': cls.get_bib_resource_type(bib),
                      'access': cls.get_access_type(bib),
                      'analytical': cls.check_is_analytical(bib),
                      'f33x': cls.get_33x_summary(bib)}

        return res_format

    @classmethod
    def get_creators(cls, bib: bib_type) -> Optional[List[str]]:
        """get_authors(bib: etree.Element) -> Option.al[List[str]]
        Get the list of authors from 100$a, 700$a

        :param bib: :class:`etree.Element`

        :return: list of authors and None if not found
        """
        fields = []
        for tag in ['100', '700']:
            fields += cls.findall(bib, f'{tag}$$a')
        if len(fields) == 0:
            return None
        else:
            unique_list = []
            for field in fields:
                if field not in unique_list:
                    unique_list.append(field)

            return unique_list

    @classmethod
    def get_corp_creators(cls, bib: bib_type) -> Optional[List[str]]:
        """get_authors(bib: etree.Element) -> Option.al[List[str]]
        Get the list of authors from 110$a, 111$a, 710$a and 711$a

        :param bib: :class:`etree.Element`

        :return: list of authors and None if not found
        """
        fields = []
        for tag in ['110', '111', '710', '711']:
            fields += cls.findall(bib, f'{tag}$$a')

        if len(fields) == 0:
            return None
        else:
            unique_list = []
            for field in fields:
                if field not in unique_list:
                    unique_list.append(field)

            return unique_list

    @classmethod
    def get_extent(cls, bib: bib_type) -> Optional[str]:
        """get_extent(bib: etree.Element)
        Return extent from field 300$a

        :param bib: :class:`etree.Element`
        :return: list of extent or None if not found
        """
        extent_field = cls.find(bib, '300$$a')

        if extent_field is not None:
            return cls.normalize_extent(extent_field)

        return None

    @classmethod
    def get_publishers(cls, bib: bib_type) -> Optional[List[str]]:
        """get_publishers(bib: etree.Element) -> Optional[List[str]]
        Return publishers from field 264$b

        :param bib: :class:`etree.Element`
        :return: list of publishers or None if not found
        """
        publishers = cls.findall(bib, '264$$b')

        return None if len(publishers) == 0 else publishers

    @classmethod
    def get_series(cls, bib: bib_type) -> Optional[List[str]]:
        """get_series(bib: etree.Element) -> Optional[List[str]]
        Return series title from field 490$a

        :param bib: :class:`etree.Element`

        :return: list of titles of related series or None if not found
        """
        series_fields = cls.findall(bib,'490$$a')
        series = None
        if len(series_fields) > 0:
            series = [cls.normalize_title(field) for field in series_fields]

        return series

    @classmethod
    def get_languages(cls, bib: bib_type) -> Optional[List[str]]:
        """get_language(bib: etree.Element) -> Optional[str]
        Return language from field 008

        :param bib: :class:`etree.Element`

        :return: language or None if not found
        """
        controlfield008 = cls.find(bib, '008')

        languages = [controlfield008[35:38]]

        for field041 in cls.findall(bib, '041$$a'):
            if field041 not in languages:
                languages.append(field041)

        return languages

    @classmethod
    def get_editions(cls, bib: bib_type) -> Optional[List[Dict]]:
        """get_editions(bib: etree.Element) -> Optional[List[str]]
        Returns a list of editions (fields 250$a and 250$b)

        :param bib: :class:`etree.Element`

        :return: list of editions or None if not found
        """
        edition_fields = cls.findall(bib, '250')

        if len(edition_fields) == 0:
            return None

        editions = []
        for edition_field in edition_fields:
            subfield_a = None
            subfield_b = None
            for subfield in edition_field:
                if 'a' in subfield:
                    subfield_a = subfield['a']
                if 'b' in subfield:
                    subfield_b = subfield['b']

            if subfield_b is not None:
                editions.append(f'{subfield_a} {subfield_b}')
            else:
                editions.append(subfield_a)

        editions_complete = []

        for edition in editions:
            # Normalize edition statement
            norm_edition = tools.to_ascii(edition)
            norm_edition = tools.remove_special_chars(norm_edition, keep_dot=True)

            for k in tools.editions_data.keys():
                norm_edition = re.sub(r'\b' + k + r'\b', str(tools.editions_data[k]), norm_edition)

            # Find all numbers in the edition statement
            numbers = sorted([int(f) for f in re.findall(r'\d+', norm_edition)])
            editions_complete.append({'nb': numbers, 'txt': edition})
        if len(editions_complete) == 0:
            return None
        else:
            return editions_complete

    @classmethod
    def get_parent(cls, bib: bib_type) -> Optional[Dict]:
        """get_parent(bib: etree.Element) -> Optional[List[str]]
        Return a dictionary with information found in field 773

        Keys of the parent dictionary:
        - title: title of the parent
        - issn: content of $x
        - isbn: content of $z
        - number: content of $g no:<content>
        - year: content of $g yr:<content> or first 4 digits numbers in a $g
        - parts: longest list of numbers in a $g

        :param bib: :class:`etree.Element`

        :return: list of parent information or None if not found
        """
        f773 = cls.find(bib, '773')

        # No 773 => no parent record
        if f773 is None:
            return None

        parent_information = dict()
        for subfield in f773:
            if 't' in subfield:
                parent_information['title'] = cls.normalize_title(subfield['t'])
            elif 'x' in subfield:
                parent_information['std_num'] = cls.normalize_issn(subfield['x'])
            elif 'z' in subfield:
                parent_information['std_num'] = cls.normalize_isbn(subfield['z'])
            elif 'g' in subfield:
                txt = subfield['g']

                # Get year information if available. In Alma year is prefixed with "yr:<year>"
                year = cls.extract_year(txt)
                if year is not None and (txt.startswith('yr:') is True or 'year' not in parent_information):
                    # if year key is not populated, populate it with available data
                    parent_information['year'] = year

                # Get number information. In Alma this information is prefixed with "nr:<number>"
                if txt.startswith('no:'):
                    parent_information['number'] = txt[3:]

                # No normalized parts in Alma format. Try to extract the longest list of numbers
                if not txt.startswith('yr:') and not txt.startswith('no:'):
                    parts = cls.normalize_extent(txt)
                    if 'parts' not in parent_information or len(parts) > len(parent_information['parts']):
                        parent_information['parts'] = parts

        if len(parent_information) > 0:
            return parent_information
        else:
            return None

    @classmethod
    def is_online(cls, bib: bib_type) -> bool:
        """
        Check if the record is an online record.

        Use field 008 and leader. Position 23 indicate if a record is online or not (values "o",
         "q", "s"). For visual material and maps it's 29 position.

        :param bib: :class:`etree.Element`

        :return: boolean indicating whether the record is online
        """
        f338b = cls.find(bib, '338$$b')
        if f338b is not None and f338b == 'cr':
            return True

        leader6 = cls.get_leader_pos67(bib)[0]
        f008 = cls.find(bib,'008')
        format_pos = 29 if leader6 in 'egkor' else 23

        return f008[format_pos] in 'oqs'

    @classmethod
    def is_micro(cls, bib: bib_type):
        """Check if the record is a microform.

        Use field 008 and leader. Position 23 indicate if a record is online or not (values "a",
         "b", "c"). For visual material and maps it's 29 position.

        :param bib: :class:`etree.Element`

        :return: boolean indicating whether the record is a micro form
        """
        leader6 = cls.get_leader_pos67(bib)[0]
        f008 = cls.find(bib,'008')
        format_pos = 29 if leader6 in 'egkor' else 23
        f338b = cls.find(bib,'338$$b')
        if f338b is not None and f338b.startswith('h') is True:
            return True

        return f008[format_pos] in 'abc'

    @classmethod
    def is_braille(cls, bib: bib_type):
        """Check if the record is a Braille document.

        Use field 008 and leader. Position 23 indicate if a record is a Braille document or not
        (values "f"). For visual material and maps it's 29 position.

        :param bib: :class:`etree.Element`

        :return: boolean indicating whether the record is a micro form
        """
        leader6 = cls.get_leader_pos67(bib)[0]
        f008 = cls.find(bib,'008')
        format_pos = 29 if leader6 in 'egkor' else 23
        f336b = cls.find(bib,'336$$b')

        if f336b is not None and f336b == 'tct':
            return True

        return f008[format_pos] in 'f'

    @classmethod
    def check_is_analytical(cls, bib: bib_type):
        """Check if the record is an analytical record.

        Leader position 7 indicates if a record is an analytical record.

        :param bib: :class:`etree.Element`

        :return: boolean indicating whether the record is an analytical record
        """
        leader7 = cls.get_leader_pos67(bib)[1]

        return leader7 == 'a'

    @classmethod
    def get_bib_info(cls, bib: bib_type):
        """get_bib_info(bib: etree.Element)
        Return a json object with the brief record information

        :param bib: :class:`etree.Element`
        :return: json object with brief record information
        """
        bib_info = {'rec_id': cls.get_rec_id(bib),
                    'format': cls.get_format(bib),
                    'titles': cls.get_titles(bib),
                    'short_titles': [title['m'] for title in cls.get_titles(bib)],
                    'creators': cls.get_creators(bib),
                    'corp_creators': cls.get_corp_creators(bib),
                    'languages': cls.get_languages(bib),
                    'extent': cls.get_extent(bib),
                    'editions': cls.get_editions(bib),
                    'years': cls.get_years(bib),
                    'publishers': cls.get_publishers(bib),
                    'series': cls.get_series(bib),
                    'parent': cls.get_parent(bib),
                    'std_nums': cls.get_std_num(bib),
                    'sys_nums': cls.get_sys_nums(bib)}
        return bib_info

class XmlBriefRecFactory(BriefRecFactory):
    """Class representing a brief record object

    This class heritates from :class:`BriefRec` and is used to create a brief record object
    from a MARCXML record.

    :cvar bib_type: :class:`etree.Element`

    """
    bib_type = etree.Element

    @classmethod
    def find(cls, bib: bib_type, path:str) -> Optional[Union[str,List[Dict]]]:
        """Find a value in the MARCXML record

        :param bib: Marc21 record
        :param path: path to the value to find

        :return: value found or None if not found
        """
        path = path.split('$$')
        path_xml = ''

        if path[0] == 'leader':
            path_xml = './/leader'

        elif path[0].startswith('00'):
            path_xml = f'.//controlfield[@tag="{path[0]}"]'

        elif len(path) == 2:
            path_xml = f'.//datafield[@tag="{path[0]}"]/subfield[@code="{path[1]}"]'

        elif len(path) == 1:
            path_xml = f'.//datafield[@tag="{path[0]}"]'
            result = bib.find(path_xml)
            if result is None:
                return None

            subfields = [{subfield.get('code'): subfield.text} for subfield in result]
            return None if len(subfields) == 0 else subfields

        result = bib.find(path_xml)

        return result.text if result is not None else None


    @classmethod
    def findall(cls, bib: bib_type, path:str) -> List[Union[str, List[Dict[str,str]]]]:
        """Find a value in the MARCXML record

        :param bib: Marc21 record
        :param path: path to the value to find

        :return: value found or None if not found
        """
        path = path.split('$$')

        if len(path) == 2:
            path_xml = f'.//datafield[@tag="{path[0]}"]/subfield[@code="{path[1]}"]'

            results = bib.findall(path_xml)

            return [result.text for result in results]

        elif len(path) == 1:
            # Transform the data to json
            path_xml = f'.//datafield[@tag="{path[0]}"]'

            results = bib.findall(path_xml)
            fields = []
            for result in results:
                fields.append([{subfield.get('code'): subfield.text} for subfield in result])
            return fields

        return []


class JsonBriefRecFactory(BriefRecFactory):
    """Class to create a brief record from a MARCXML record

    The class can parse several fields of the MARCXML record. It can also
    summarize the result in a json object.

    :cvar bib_type: :class:`Dict`
    """

    bib_type = Dict

    @classmethod
    def find(cls, bib: bib_type, path: str) -> Optional[Union[str, List[Dict]]]:
        """Find a value in the MARCXML record

        :param bib: Marc21 record
        :param path: path to the value to find

        :return: value found or None if not found
        """
        path = path.split('$$')

        if path[0] == 'leader':
            return bib['marc']['leader']

        elif path[0].startswith('00'):
            return bib['marc'].get(path[0])

        elif len(path) == 2:
            datafields = bib['marc'].get(path[0], [])

            for datafield in datafields:
                for subfield in datafield['sub']:
                    if path[1] in subfield:
                        return subfield[path[1]]

        elif len(path) == 1:
            datafields = bib['marc'].get(path[0])
            if datafields is not None:
                return datafields[0]['sub']

        return None

    @classmethod
    def findall(cls, bib: bib_type, path: str) -> List[Union[str, List[Dict]]]:
        """Find a value in the MARCXML record

        :param bib: Marc21 record
        :param path: path to the value to find

        :return: value found or None if not found
        """
        path = path.split('$$')

        if len(path) == 2:
            values = []
            datafields = bib['marc'].get(path[0], [])
            for datafield in datafields:
                for subfield in datafield['sub']:
                    if path[1] in subfield:
                        values.append(subfield[path[1]])
            return values

        elif len(path) == 1:
            fields = bib['marc'].get(path[0], [])
            return [field['sub'] for field in fields]

        return []