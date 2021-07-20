from collections import namedtuple

__author__ = 'minjoon'


Question = namedtuple("Question", "key text sentence_words sentence_expressions diagram_path choice_words choice_expressions answer choices")
