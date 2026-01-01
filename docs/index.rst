********************************
dedupmarcxml documentation |doc|
********************************

.. toctree::

   briefrecord

.. |doc| image:: https://readthedocs.org/projects/dedupmarcxml/badge/?version=latest
    :target: https://dedupmarcxml.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status



How to import modules
---------------------

.. code-block:: python

    # Import libraries
    from dedupmarcxml.evaluate import evaluate_records_similarity, get_similarity_score
    from dedupmarcxml.briefrecord import Briefrec


Base example code
-----------------

.. code-block:: python

    # Import libraries
    from dedupmarcxml.evaluate import evaluate_records_similarity, get_similarity_score
    from dedupmarcxml.briefrecord import BriefRec

    rec1 = BriefRec(etree.Element)
    rec2 = BriefRec(etree.Element)

    score_detailed = evaluate_records_similarity(rec1, rec2, method=mean)

    score = get_similarity_score(score_detailed, method='mean')


Contents
--------

.. toctree::
   :maxdepth: 1

.. autoclass:: dedupmarcxml.briefrecord::BriefRec
  :members:

.. autofunction:: dedupmarcxml.evaluate::evaluate_records_similarity

.. autofunction:: dedupmarcxml.evaluate::get_similarity_score

