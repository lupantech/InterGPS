from geosolver.ontology.ontology_definitions import VariableSignature, FormulaNode, signatures, \
    high_order_type_inheritances

__author__ = 'minjoon'


def augment_formulas(formulas):
    """
    square variable -> quad, and add IsSquare(quad)

    :param formulas:
    :return:
    """
    new_formulas = set()
    tester = lambda node: isinstance(node.signature, VariableSignature)
    getter = lambda node: _update(new_formulas, node)
    for formula in formulas:
        assert isinstance(formula, FormulaNode)
        new_formula = formula.replace_node(tester, getter)
        new_formulas.add(new_formula)
    return new_formulas


def _update(formulas, variable):
    assert isinstance(formulas, set)
    assert isinstance(variable, FormulaNode)
    assert isinstance(variable.signature, VariableSignature)
    for from_, to, id_ in high_order_type_inheritances:
        if from_ == variable.return_type:
            new_variable = FormulaNode(VariableSignature(variable.signature.id, to, name=variable.signature.name), [])
            formula = FormulaNode(signatures[id_], [new_variable])
            formulas.add(formula)
            return new_variable
    return variable

