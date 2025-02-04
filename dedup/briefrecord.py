from lxml import etree
from typing import List, Optional, Dict
import re
import tools
import logging
import json


class BriefRec:
    """Class representing a brief record object

    You can create a brief record object from a :class:`SruRecord` object or
    from the XML data of a MARCXML record using an Etree Element object.

    The namespaces are removed from the XML data.

    :ivar error: boolean, is True in case of error
    :ivar error_messages: list of string with the error messages
    :ivar data: json object with brief record information
    :ivar src_data: XML data of the record

    """

    def __init__(self, rec: etree.Element) -> None:
        """Brief record object

        :param rec: XML data of the record or :class:`SruRecord` object
        """
        self.error = False
        self.error_messages = []
        self.data = None

        if rec.__class__.__name__ == '_Element':
            self.src_data = tools.remove_ns(rec)
            self.data = self._get_bib_info()
        else:
            self.error = True
            self.error_messages.append(f'Wrong type of data provided: {type(rec)}')
            logging.error(f'BriefRec: wrong type of data provided: {type(rec)}')

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

    # @check_error
    def _get_bib_info(self):
        bib_info = BriefRecFactory.get_bib_info(self.src_data)
        return bib_info


class BriefRecFactory:
    """Class to create a brief record from a MARCXML record

    The class can parse several fields of the MARCXML record. It can also
    summarize the result in a json object.
    """

    @staticmethod
    def normalize_title(title: str) -> str:
        """normalize_title(title: str) -> str
        Normalize title string

        Idea is to remove "<<" and ">>" of the title and remove
        all non-alphanumeric characters.

        :param title: title to normalize

        :return: string with normalized title
        """
        title = title.replace('<<', '').replace('>>', '')
        return title

    @staticmethod
    def normalize_extent(extent: str) -> Optional[Dict]:
        """Normalize extent string and return a dictionary with numbers

        :param extent: extent to normalize

        :return: a dictionary with keys 'nb' and 'txt'
        """
        extent_lower = extent.lower()
        extent_list = [int(f) for f in re.findall(r'\d+', extent_lower)]
        extent_list += [tools.roman_to_int(f) for f in re.findall(r'\b[ivxlcdm]+\b', extent_lower)
                        if tools.roman_to_int(f) is not None]

        return {'nb': sorted(extent_list, reverse=True), 'txt': extent}

    @staticmethod
    def normalize_isbn(isbn: str) -> Optional[str]:
        """Suppress hyphen and textual information of the provided isbn

        :param isbn: raw string containing isbn

        :return: string containing normalized isbn
        """
        # Remove hyphens and all textual information about isbn
        m = re.search(r'\d{8,}[\dxX]', isbn.replace('-', ''))
        if m is not None:
            return m.group()

    @staticmethod
    def normalize_issn(issn: str) -> Optional[str]:
        """Suppress hyphen and textual information of the provided issn

        :param issn: raw string containing issn

        :return: string containing normalized issn
        """
        # Remove hyphens and all textual information about isbn
        m = re.search(r'\d{7}[\dxX]', issn.replace('-', ''))
        if m is not None:
            return m.group()

    @staticmethod
    def extract_year(txt: str) -> Optional[int]:
        """extract_year(str) -> Optional[int]
        Extract a substring of 4 digits

        :param txt: string to parse to get year

        :return: int value with the found year or None if no year available
        """
        m = re.search(r'\b\d{4}\b', txt)
        if m is not None:
            return int(m.group())

    @staticmethod
    def get_rec_id(bib: etree.Element) -> Optional[str]:
        """get_rec_id(bib: etree.Element) -> Optional[str]
        get_rec_id(bib) -> Optional[str]
        Get the record ID

        :param bib: :class:`etree.Element`

        :return: record ID or None if not found
        """
        controlfield001 = bib.find('.//controlfield[@tag="001"]')
        if controlfield001 is None:
            return None
        return controlfield001.text

    @staticmethod
    def get_std_num(bib: etree.Element) -> Optional[List[str]]:
        """get_other_std_num(bib: etree.Element) -> Optional[List[str]]
        Get a list of standardized numbers like DOI

        :param bib: :class:`etree.Element`

        :return: set of standardized numbers
        """

        # Get isbn fields
        fields = bib.findall('.//datafield[@tag="020"]/subfield[@code="a"]')
        raw_isbns = set([field.text for field in fields])
        isbns = set()

        for raw_isbn in raw_isbns:
            isbn = BriefRecFactory.normalize_isbn(raw_isbn)
            if isbn is not None:
                isbns.add(isbn)

        # Get ISSN fields
        fields = bib.findall('.//datafield[@tag="022"]/subfield[@code="a"]')
        raw_issns = set([field.text for field in fields])
        issns = set()

        for raw_issn in raw_issns:
            issn = BriefRecFactory.normalize_issn(raw_issn)
            if issn is not None:
                issns.add(issn)

        # Get other standardized numbers
        fields = bib.findall('.//datafield[@tag="024"]/subfield[@code="a"]')
        std_nums = set([field.text for field in fields])

        # Get other publisher numbers
        fields = bib.findall('.//datafield[@tag="028"]/subfield[@code="a"]')
        pub_nums = set([field.text for field in fields])

        if len(isbns) == 0 and len(issns) == 0 and len(std_nums) == 0 and pub_nums == 0:
            return None

        return list(set.union(isbns, issns, std_nums, pub_nums))

    @staticmethod
    def get_leader_pos67(bib: etree.Element) -> Optional[str]:
        """get_leader_pos67(bib: etree.Element) -> Optional[str]
        Get the leader position 6 and 7

        Used to determine the format of the record

        :param bib: :class:`etree.Element`

        :return: leader position 6 and 7 or None if not found
        """

        leader = bib.find('.//leader')
        if leader is not None:
            return leader.text[6:8]

    @staticmethod
    def get_sys_nums(bib: etree.Element) -> Optional[List[str]]:
        """get_sysnums(bib: etree.Element) -> Optional[List[str]]
        Get a set of system numbers

        :param bib: :class:`etree.Element`

        :return: set of system numbers
        """
        fields = bib.findall('.//datafield[@tag="035"]/subfield[@code="a"]')
        sys_nums = set([field.text for field in fields])
        if len(sys_nums) == 0:
            return None

        return list(sys_nums)

    @staticmethod
    def get_title(bib: etree.Element) -> Optional[str]:
        """Get normalized content of 245$a

        :param bib: :class:`etree.Element`

        :return: normalized content of field 245$a
        """
        title_field = bib.find('.//datafield[@tag="245"]/subfield[@code="a"]')
        if title_field is not None:
            return BriefRecFactory.normalize_title(title_field.text)

    @staticmethod
    def get_subtitle(bib: etree.Element) -> Optional[str]:
        """get_subtitle(bib: etree.Element) -> Optional[str]
        Get normalized content of 245$b

        :param bib: :class:`etree.Element`

        :return: normalized content of field 245$b or None if not found
        """

        sub_title_field = bib.find('.//datafield[@tag="245"]/subfield[@code="b"]')
        if sub_title_field is not None:
            return BriefRecFactory.normalize_title(sub_title_field.text)

    @staticmethod
    def get_part_title(bib: etree.Element) -> Optional[str]:
        """get_part_title(bib: etree.Element) -> Optional[str]

        :param bib: :class:`etree.Element`

        :return: content of 245$p or None if not found
        """
        part_title_field = bib.find('.//datafield[@tag="245"]/subfield[@code="p"]')
        if part_title_field is not None:
            return BriefRecFactory.normalize_title(part_title_field.text)

    @staticmethod
    def get_all_varying_titles(bib: etree.Element) -> Optional[List[str]]:
        """get_all_varying_titles(bib: etree.Element) -> Optional[List[str]]
        Get all varying titles from 246 fields

        :param bib: :class:`etree.Element`

        :return: list of varying titles or None if not found
        """
        fields = bib.findall('.//datafield[@tag="246"]')

        titles = []
        for field in fields:
            title = ''
            subf_a = field.find('subfield[@code="a"]')
            if subf_a is not None:
                title += subf_a.text
            subf_b = field.find('subfield[@code="b"]')
            if subf_b is not None:
                title += ' ' + subf_b.text
            subf_p = field.find('subfield[@code="p"]')
            if subf_p is not None:
                title += ' ' + subf_p.text
            if len(title) > 0:
                titles.append(BriefRecFactory.normalize_title(title))

        return titles

    @staticmethod
    def get_complete_titles(bib: etree.Element) -> Optional[List[str]]:
        """
        Get the complete titles of the record

        :param bib: :class:`etree.Element`

        :return: list of complete titles or None if not found

        """
        title245 = ' '.join([t for t in [BriefRecFactory.get_title(bib),
                                         BriefRecFactory.get_subtitle(bib),
                                         BriefRecFactory.get_part_title(bib)] if t is not None])

        titles246 = BriefRecFactory.get_all_varying_titles(bib)
        titles = [title245] + titles246
        return titles if len(titles) > 0 else None

    @staticmethod
    def get_years(bib: etree.Element) -> Optional[Dict]:
        """Get the dates of publication from 008 and 264$$c fields

        This function retrieves the publication years from the 008 control
        field and the 264$c data field of a MARC record. 264c is only used when
        different of 008.

        :param bib: :class:`etree.Element`

        :return: dictionary with keys 'year1' and optionally 'year2', or None if no year is found
        """
        controlfield008 = bib.find('.//controlfield[@tag="008"]')
        field_264c = bib.find('.//datafield[@tag="264"]/subfield[@code="c"]')

        year1 = []
        year2 = None

        # Check source 1: 008
        if controlfield008 is not None:
            year1_008 = BriefRecFactory.extract_year(controlfield008.text[7:11])
            if year1_008 is not None:
                year1.append(year1_008)
            year2_008 = BriefRecFactory.extract_year(controlfield008.text[11:15])
            if year2_008 is not None:
                year2 = year2_008

        # Check source 2: 264$$c
        if field_264c is not None:
            year1_264c = BriefRecFactory.extract_year(field_264c.text)

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

    @staticmethod
    def get_33x_summary(bib: etree.Element) -> Optional[str]:
        """ get_33x_summary(bib: etree.Element) -> Optional[str]
        Get a summary of the 336, 337 and 338 fields

        :param bib: :class:`etree.Element`

        :return: summary of the 336, 337 and 338 fields"""
        s = ''
        for tag in ['336', '337', '338']:
            fields = bib.findall(f'.//datafield[@tag="{tag}"]/subfield[@code="b"]')
            if len(fields) > 0:
                s += ','.join([f.text for f in fields]) + ';'
            else:
                s += ' ;'
        s = s[:-1]  # remove last ; character
        return s

    @staticmethod
    def get_bib_resource_type(bib: etree.Element) -> str:
        """Get the resource type of the record

        The analyse is mainly based on the leader position 6 and 7.
        To distinguish between series and journal, we use the field
        008 pos. 6.

        :param bib: :class:`etree.Element`

        :return: resource type of the record
        """

        pos6, pos7 = BriefRecFactory.get_leader_pos67(bib)
        if pos6 in 'a':
            if pos7 in 'acdm':
                return 'Book'
            elif pos7 in 'bis':
                if BriefRecFactory.get_field_008(bib)[21] in 'pn':
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
            return 'Objet'

        elif pos6 in 'g':
            return 'Video'

        elif pos6 in 'p':
            return 'Mixed Material'

        return 'Book'

    @staticmethod
    def get_field_008(bib: etree.Element) -> Optional[str]:
        """get_008_pos_form_item(bib: etree.Element) -> Optional[str]
        Get the 008 field

        :param bib: :class:`etree.Element`

        :return: 008 field
        """
        controlfield008 = bib.find('.//controlfield[@tag="008"]')
        if controlfield008 is None:
            return None

        return controlfield008.text

    @staticmethod
    def get_access_type(bib: etree.Element) -> Optional[str]:
        """get_access_type(bib: etree.Element) -> Optional[str]
        Get the access type of the record

        :param bib: :class:`etree.Element`

        :return: access type of the record
        """
        if BriefRecFactory.check_is_micro(bib) is True:
            return 'Microform'
        if BriefRecFactory.check_is_online(bib) is True:
            return 'Online'
        if BriefRecFactory.check_is_braille(bib) is True:
            return 'Braille'

        return 'Physical'

    @staticmethod
    def get_format(bib: etree.Element) -> Dict:
        """get_format(bib: etree.Element) -> Optional[str]
        Get the format of the record from leader field position 6 and 7

        :param bib: :class:`etree.Element`

        :return: format of the record
        """
        res_format = {'type': BriefRecFactory.get_bib_resource_type(bib),
                      'access': BriefRecFactory.get_access_type(bib),
                      'analytical': BriefRecFactory.check_is_analytical(bib),
                      'summary_33x': BriefRecFactory.get_33x_summary(bib)}

        return res_format

    @staticmethod
    def get_creators(bib: etree.Element) -> Optional[List[str]]:
        """get_authors(bib: etree.Element) -> Option.al[List[str]]
        Get the list of authors from 100$a, 700$a

        :param bib: :class:`etree.Element`

        :return: list of authors and None if not found
        """
        fields = []
        for tag in ['100', '700']:
            fields += bib.findall(f'.//datafield[@tag="{tag}"]/subfield[@code="a"]')
        fields = [f.text for f in fields]
        if len(fields) == 0:
            return None
        else:
            return list(set(fields))

    @staticmethod
    def get_corp_creators(bib: etree.Element) -> Optional[List[str]]:
        """get_authors(bib: etree.Element) -> Option.al[List[str]]
        Get the list of authors from 110$a, 111$a, 710$a and 711$a

        :param bib: :class:`etree.Element`

        :return: list of authors and None if not found
        """
        fields = []
        for tag in ['110', '111', '710', '711']:
            fields += bib.findall(f'.//datafield[@tag="{tag}"]/subfield[@code="a"]')
        fields = [f.text for f in fields]
        if len(fields) == 0:
            return None
        else:
            return list(set(fields))

    @staticmethod
    def get_extent(bib: etree.Element) -> Optional[str]:
        """get_extent(bib: etree.Element)
        Return extent from field 300$a

        :param bib: :class:`etree.Element`
        :return: list of extent or None if not found
        """
        extent_field = bib.find('.//datafield[@tag="300"]/subfield[@code="a"]')
        extent = None
        if extent_field is not None:
            extent = BriefRecFactory.normalize_extent(extent_field.text)

        return extent

    @staticmethod
    def get_publishers(bib: etree.Element) -> Optional[List[str]]:
        """get_publishers(bib: etree.Element) -> Optional[List[str]]
        Return publishers from field 264$b

        :param bib: :class:`etree.Element`
        :return: list of publishers or None if not found
        """
        publisher_fields = bib.findall('.//datafield[@tag="264"]/subfield[@code="b"]')
        publishers = None
        if len(publisher_fields) > 0:
            publishers = [field.text for field in publisher_fields]

        return publishers

    @staticmethod
    def get_series(bib: etree.Element) -> Optional[List[str]]:
        """get_series(bib: etree.Element) -> Optional[List[str]]
        Return series title from field 490$a

        :param bib: :class:`etree.Element`

        :return: list of titles of related series or None if not found
        """
        series_fields = bib.findall('.//datafield[@tag="490"]/subfield[@code="a"]')
        series = None
        if len(series_fields) > 0:
            series = [BriefRecFactory.normalize_title(field.text) for field in series_fields]

        return series

    @staticmethod
    def get_languages(bib: etree.Element) -> Optional[List[str]]:
        """get_language(bib: etree.Element) -> Optional[str]
        Return language from field 008

        :param bib: :class:`etree.Element`

        :return: language or None if not found
        """
        controlfield008 = bib.find('.//controlfield[@tag="008"]')
        if controlfield008 is None:
            return None

        languages = []
        languages.append(controlfield008.text[35:38])

        for field041 in bib.findall('.//datafield[@tag="041"]/subfield[@code="a"]'):
            if field041.text not in languages:
                languages.append(field041.text)

        return languages

    @staticmethod
    def get_editions(bib: etree.Element) -> Optional[List[Dict]]:
        """get_editions(bib: etree.Element) -> Optional[List[str]]
        Returns a list of editions (fields 250$a and 250$b)

        :param bib: :class:`etree.Element`

        :return: list of editions or None if not found
        """
        edition_fields = bib.findall('.//datafield[@tag="250"]/subfield[@code="a"]')

        if len(edition_fields) == 0:
            return None

        editions = []
        for edition_field in edition_fields:
            subfield_b = edition_field.getparent().find('subfield[@code="b"]')
            if subfield_b is not None:
                editions.append(f'{edition_field.text} {subfield_b.text}')
            else:
                editions.append(edition_field.text)

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

    @staticmethod
    def get_parent(bib: etree.Element) -> Optional[Dict]:
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
        f773 = bib.find('.//datafield[@tag="773"]')

        # No 773 => no parent record
        if f773 is None:
            return None

        parent_information = dict()
        for code in ['g', 't', 'x', 'z']:
            for subfield in f773.findall(f'subfield[@code="{code}"]'):
                if code == 't':
                    parent_information['title'] = BriefRecFactory.normalize_title(subfield.text)
                elif code == 'x':
                    parent_information['issn'] = BriefRecFactory.normalize_issn(subfield.text)
                elif code == 'z':
                    parent_information['isbn'] = BriefRecFactory.normalize_isbn(subfield.text)
                elif code == 'g':
                    txt = subfield.text

                    # Get year information if available. In Alma year is prefixed with "yr:<year>"
                    year = BriefRecFactory.extract_year(txt)
                    if year is not None and (txt.startswith('yr:') is True or 'year' not in parent_information):
                        # if year key is not populated, populate it with available data
                        parent_information['year'] = year

                    # Get number information. In Alma this information is prefixed with "nr:<number>"
                    if txt.startswith('no:'):
                        parent_information['number'] = txt[3:]

                    # No normalized parts in Alma format. Try to extract the longest list of numbers
                    if not txt.startswith('yr:') and not txt.startswith('no:'):
                        parts = BriefRecFactory.normalize_extent(txt)
                        if 'parts' not in parent_information or len(parts) > len(parent_information['parts']):
                            parent_information['parts'] = parts

        if len(parent_information) > 0:
            return parent_information
        else:
            return None

    @staticmethod
    def check_is_online(bib: etree.Element):
        """check_is_online(bib:etree.Element)
        Check if the record is an online record.

        Use field 008 and leader. Position 23 indicate if a record is online or not (values "o",
         "q", "s"). For visual material and maps it's 29 position.

        :param bib: :class:`etree.Element`

        :return: boolean indicating whether the record is online
        """
        leader6 = BriefRecFactory.get_leader_pos67(bib)[0]
        f008 = bib.find('.//controlfield[@tag="008"]').text
        format_pos = 29 if leader6 in ['e', 'g', 'k', 'o', 'r'] else 23
        f338b = bib.find('.//datafield[@tag="338"]/subfield[@code="b"]')
        if f338b is not None and f338b.text == 'cr':
            return True

        return f008[format_pos] in ['o', 'q', 's']

    @staticmethod
    def check_is_micro(bib: etree.Element):
        """Check if the record is a microform.

        Use field 008 and leader. Position 23 indicate if a record is online or not (values "a",
         "b", "c"). For visual material and maps it's 29 position.

        :param bib: :class:`etree.Element`

        :return: boolean indicating whether the record is a micro form
        """
        leader6 = BriefRecFactory.get_leader_pos67(bib)[0]
        f008 = bib.find('.//controlfield[@tag="008"]').text
        format_pos = 29 if leader6 in ['e', 'g', 'k', 'o', 'r'] else 23
        f338b = bib.find('.//datafield[@tag="338"]/subfield[@code="b"]')
        if f338b is not None and f338b.text.startswith('h') is True:
            return True

        return f008[format_pos] in ['a', 'b', 'c']

    @staticmethod
    def check_is_braille(bib: etree.Element):
        """Check if the record is a Braille document.

        Use field 008 and leader. Position 23 indicate if a record is a Braille document or not
        (values "f"). For visual material and maps it's 29 position.

        :param bib: :class:`etree.Element`

        :return: boolean indicating whether the record is a micro form
        """
        leader6 = BriefRecFactory.get_leader_pos67(bib)[0]
        f008 = bib.find('.//controlfield[@tag="008"]').text
        format_pos = 29 if leader6 in ['e', 'g', 'k', 'o', 'r'] else 23
        f336b = bib.find('.//datafield[@tag="336"]/subfield[@code="b"]')

        if f336b is not None and f336b.text == 'tct':
            return True

        return f008[format_pos] in 'f'

    @staticmethod
    def check_is_analytical(bib: etree.Element):
        """Check if the record is an analytical record.

        Leader position 7 indicates if a record is an analytical record.

        :param bib: :class:`etree.Element`

        :return: boolean indicating whether the record is an analytical record
        """
        leader7 = BriefRecFactory.get_leader_pos67(bib)[1]

        return leader7 == 'a'

    @staticmethod
    def get_bib_info(bib: etree.Element):
        """get_bib_info(bib: etree.Element)
        Return a json object with the brief record information

        :param bib: :class:`etree.Element`
        :return: json object with brief record information
        """
        bib_info = {'rec_id': BriefRecFactory.get_rec_id(bib),
                    'format': BriefRecFactory.get_format(bib),
                    'titles': BriefRecFactory.get_complete_titles(bib),
                    'short_title': BriefRecFactory.get_title(bib),
                    'creators': BriefRecFactory.get_creators(bib),
                    'corp_creators': BriefRecFactory.get_corp_creators(bib),
                    'languages': BriefRecFactory.get_languages(bib),
                    'extent': BriefRecFactory.get_extent(bib),
                    'editions': BriefRecFactory.get_editions(bib),
                    'years': BriefRecFactory.get_years(bib),
                    'publishers': BriefRecFactory.get_publishers(bib),
                    'series': BriefRecFactory.get_series(bib),
                    'parent': BriefRecFactory.get_parent(bib),
                    'std_nums': BriefRecFactory.get_std_num(bib),
                    'sys_nums': BriefRecFactory.get_sys_nums(bib)}
        return bib_info
