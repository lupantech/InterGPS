from geosolver.expression.expression_parser import expression_parser
from geosolver.expression.prefix_to_formula import prefix_to_formula
from geosolver.grounding.states import MatchParse
from geosolver.ontology.ontology_definitions import FormulaNode, issubtype, VariableSignature, signatures, FunctionSignature
from geosolver.utils.num import is_number

__author__ = 'minjoon'


def parse_match_formulas(match_parse):
    assert isinstance(match_parse, MatchParse)
    match_atoms = []
    for label, terms in match_parse.match_dict.iteritems():
        for term in terms:
            assert isinstance(term, FormulaNode)
            if issubtype(term.return_type, 'entity'):
                if term.signature.id == "Angle":
                    res = FormulaNode(signatures['Ge'], [FormulaNode(signatures['Pi'], []), FormulaNode(signatures['MeasureOf'], [term])])
                    match_atoms.append(res)
                continue

            # FIXME : to be obtained by tag model

            left_term = prefix_to_formula(expression_parser.parse_prefix(label))

            """
            if is_number(label):
                left_term = FormulaNode(FunctionSignature(label, "number", []), [])
            else:
                vs = VariableSignature(label, 'number')
                left_term = FormulaNode(vs, [])
            """

            atom = FormulaNode(signatures['Equals'], [left_term, term])
            match_atoms.append(atom)

            if term.signature.id == "Div":
                # TODO : this should be only constrained if the observed angle is < 180
                # TODO : In fact, the labeling should be reorganized. (x --> x*\degree)
                res = FormulaNode(signatures['Ge'], [180, left_term])
                match_atoms.append(res)


    return match_atoms
