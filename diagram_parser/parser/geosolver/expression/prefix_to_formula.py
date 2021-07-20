from geosolver.ontology.ontology_definitions import FormulaNode, VariableSignature, abbreviations, signatures, FunctionSignature
from geosolver.utils.num import is_number

__author__ = 'minjoon'

def prefix_to_formula(prefix):
    """

    :param list prefix:
    :return FormulaNode:
    """
    if isinstance(prefix, str):
        if prefix in abbreviations:
            return FormulaNode(signatures[abbreviations[prefix]], [])
        elif is_number(prefix):
            return FormulaNode(FunctionSignature(prefix, 'number', []), [])
        else:
            return FormulaNode(VariableSignature(prefix, 'number'), [])
    else:
        sig = signatures[abbreviations[prefix[0]]]
        children = [prefix_to_formula(child) for child in prefix[1:]]
        for idx, child in enumerate(children):
            child.signature.return_type = sig.arg_types[idx]
            child.return_type = sig.arg_types[idx]
        out = FormulaNode(sig, children)
        return out
