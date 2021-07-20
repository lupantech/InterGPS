from geosolver.expression.expression_parser import expression_parser
from geosolver.expression.prefix_to_formula import prefix_to_formula
from geosolver.utils.prep import sentence_to_words_statements_values

__author__ = 'minjoon'

def test_prefix_to_formula():
    string = "2*\degree"
    prefix = expression_parser.parse_prefix(string)
    print prefix
    formula = prefix_to_formula(prefix)
    print(formula)

def test_prep():
    paragraph = r"a=5"
    words, statements, values = sentence_to_words_statements_values(paragraph)
    print " ".join(words.values())
    for expression in statements + values:
        prefix = expression_parser.parse_prefix(expression)
        formula = prefix_to_formula(prefix)
        print formula

if __name__ == "__main__":
    test_prefix_to_formula()
