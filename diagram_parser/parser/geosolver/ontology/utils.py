from geosolver.ontology.ontology_definitions import SetNode, VariableSignature, FormulaNode

__author__ = 'minjoon'

CRITERIA = ['Three', 'IsAngle', 'IsPoint', 'IsLine', 'IsCircle', 'IsPolygon', 'IsTriangle', 'IsQuad', 'IsHexagon', 'IntersectAt']

def flatten_formulas(formulas):
    out = []
    for formula in formulas:
        if isinstance(formula, SetNode):
            out.extend(formula.children)
        else:
            out.append(formula)
    return out

def filter_formulas(formulas, criteria=None):
    if criteria is None:
        criteria = CRITERIA
    out = []
    for formula in formulas:
        if not formula.signature.id in criteria:
            out.append(formula)
    return out

def reduce_formulas(formulas):
    """
    Equals(m, 5), Equals(m, l) --> Equals(5, l)
    Idea: if we find something like m = 40, we replace m with 40 for every formula
    Optional thing for boosting solver speed.
    :param formulas:
    :return:
    """
    variable_values = {}
    for formula in formulas:
        if formula.signature.id != "Equals":
            continue
        left, right = formula.children
        if left.is_grounded(['What', 'Which']):
            left, right = right, left

        if isinstance(left.signature, VariableSignature) and right.is_grounded(['What', 'Which']):
            variable_values[left.signature] = right

    tester = lambda node: isinstance(node, FormulaNode) and node.signature in variable_values
    getter = lambda node: variable_values[node.signature]
    replaced_formulas = [formula.replace_node(tester, getter) for formula in formulas]
    filtered_formulas = [formula for formula in replaced_formulas if not formula.is_grounded()]
    return filtered_formulas

