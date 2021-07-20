from zipfile import ZipFile

from geosolver.database.states import Question
from geosolver.utils.prep import get_number_string

__author__ = 'minjoon'


def zip_diagrams(questions, dest):
    """
    zip just the diagrams in the questions
    and save the file in the destination

    :param dict questions:
    :param str dest:
    :return:
    """
    with ZipFile(dest, 'w') as myzip:
        for key, question in questions.iteritems():
            assert isinstance(question, Question)
            number_string = get_number_string(int(question.key), 4)
            myzip.write(question.diagram_path, "%s.png" % number_string)
    return True


def zip_questions(questions, dest):
    """
    zip all information about the questions

    :param questions:
    :param dest:
    :return:
    """


def split(dicts, mid, end=1):
    keys = dicts[0].keys()
    bk = int(mid*len(keys))
    ep = int(end*len(keys))
    left_keys = keys[:bk]
    right_keys = keys[bk:ep]
    left = tuple({pk: d[pk] for pk in left_keys} for d in dicts)
    right = tuple({pk: d[pk] for pk in right_keys} for d in dicts)
    return left, right
