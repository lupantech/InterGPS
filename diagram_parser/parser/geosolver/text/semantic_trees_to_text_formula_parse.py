from geosolver.ontology.ontology_definitions import FormulaNode
from geosolver.text.states import TextFormulaParse

__author__ = 'minjoon'

def semantic_trees_to_text_formula_parse(semantic_trees):
    formulas = [annotation_node.to_formula() for annotation_node in semantic_trees]
    core_formulas = []
    cc_formulas = []
    for formula in formulas:
        assert isinstance(formula, FormulaNode)
        if formula.signature.id == "Is":
            is_formulas.append(formula)
        elif formula.signature.id == 'CC':
            cc_formulas.append(formula)
        else:
            core_formulas.append(formula)
    text_formula_parse = TextFormulaParse(core_formulas, is_formulas, cc_formulas)
    return text_formula_parse
