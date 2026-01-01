
Brief record format
===================

Deduplication is based on a simplified representation of the bibliographic record, called a "brief record". This brief record contains only the most relevant fields for deduplication purposes, omitting less critical details.
The structure of a brief record is as follows:

.. code-block:: json

    {
      "rec_id": "991089939809705501",
      "format": {
        "type": "Book",
        "access": "Physical",
        "analytical": false,
        "f33x": "txt;n;nc"
      },
      "titles": [
        {
          "m": "Russkij jazyk dlya vtorogo i tret'ego goda obuchenija",
          "s": ""
        }
      ],
      "short_titles": [
        "Russkij jazyk dlya vtorogo i tret'ego goda obuchenija"
      ],
      "creators": [
        "Kozlova, L. A."
      ],
      "corp_creators": null,
      "languages": [
        "rus"
      ],
      "extent": {
        "nb": [
          637
        ],
        "txt": "637 S."
      },
      "editions": null,
      "years": {
        "y1": [
          1996
        ]
      },
      "publishers": [
        "Russkij jazyk"
      ],
      "series": null,
      "parent": null,
      "std_nums": [
        "520001767X"
      ],
      "sys_nums": [
        "(swissbib)232025495-41slsp_network"
      ]
    }

:rec_id:
    String, unique identifier of the record.
    Example: ``"991089939809705501"``

:format:

    Dictionary with information about the format of the document.

    - **type** *(string)*: Type of resource, possible values include:
        - ``Book``
        - ``Journal``
        - ``Series``
        - ``Notated Music``
        - ``Audio``
        - ``Map``
        - ``Manuscript``
        - ``Image``
        - ``Object``
        - ``Video``
        - ``Mixed Material``
        - ``Other``

    - **access** *(string)*:
        - ``Physical``
        - ``Online``
        - ``Microform``
        - ``Braille``

    - **analytical** *(boolean)*: Indicates whether the document is analytical

    - **f33x** *(string)*: MARC or internal format code (e.g. ``txt;n;nc``)

:titles:
    Array of dictionaries with titles of the document

    - **m** *(string)*: Main title
    - **s** *(string)*: Subtitle (often empty)

:short_titles:
    Array of strings. Uses ``245$$a``, ``$$b``, ``$$p`` and ``246$$a``, ``$$b``, ``$$p`` fields
    Main part of the titles (without subtitles)

:creators:
    Null or array of strings. Uses ``100$$a``, ``700$$a`` fields.
    Authors of the document

:corp_creators:
    Null or array of strings. Uses ``110$$a``, ``111$$a``, ``710$$a``, ``711$$a`` fields.
    Institutional authors (often null if not applicable).

:languages:
    Array of strings. Uses ``008`` positions 35-37 and ``041$$a`` field.
    Languages of the document, ISO codes (e.g. ``rus`` for Russian).

:extent:
    Object containing information about the physical or textual extent.
    Uses ``300`` field.

    - **nb** *(array of integers)*: list of numbers used to describe the document
    - **txt** *(string)*: Textual description (e.g. ``637 S.``)

:editions:
    Null or array.
    Edition information (null if not provided).

:years:
    Object containing publication years. Uses ``264$$c`` field and ``008`` positions 7-14.

    - **y1** *(array of integers)*: Publication years (e.g. ``[1996]``)
    - **y2** *(array of integers)*: Additional years (often null)

:publishers:
    List of strings. USes ``264$$b`` field.
    Name(s) of the publisher (e.g. ``"Russkij jazyk"``).

:series:
    Null or list, use ``490$$a`` field
    Editorial series (null if not provided).

:parent:
    Null or dictionary. It uses the ``773`` field information

    - **title** *(string)*: Title of the parent document.
        - **issn** *(string)*: Content of subfield ``$$x``.
        - **isbn** *(string)*: Content of subfield ``$$z``.
        - **number** *(string)*: Content of subfield $g with prefix ``no:<content>``.
        - **year** *(string)*: Content of subfield ``$$g`` with prefix ``yr:<content>``, or the first 4-digit number found in $g.
        - **parts** *(array of integers)*: try to extract numbers in subfield ``$$g``.

:std_nums:
    List of strings.
    Standard numbers such as ISBN. Source: ``020$$a``, ``022$$a``, ``024$$a``, ``028$$a``. Numbers are normalized.

:sys_nums:
    List of strings.
    System numbers, all ``035$$a`` values (e.g. ``(swissbib)232025495-41slsp_network"``).