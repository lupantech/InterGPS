import re

import networkx as nx

from geosolver.ontology.ontology_definitions import FormulaNode, VariableSignature, SetNode, issubtype, signatures

__author__ = 'minjoon'


def complete_formulas(core_formulas, cc_formulas):
    # ised_formulas = _apply_is(text_formula_parse.is_formulas, text_formula_parse.core_formulas)
    cced_formulas = _apply_cc(cc_formulas, core_formulas)
    return cced_formulas

def _apply_is(is_formulas, core_formulas):
    """
    Given a list of formulas, resolve transitivity by Is relation

    :param formula_nodes:
    :return:
    """
    graph = nx.Graph()
    explicit_sigs = set()
    equal_formulas = []
    for formula_node in is_formulas:
        assert isinstance(formula_node, FormulaNode)
        a_node, b_node = formula_node.children
        a_sig, b_sig = a_node.signature, b_node.signature

        if a_sig.return_type == 'number' or b_sig.return_type == 'number':
            equal_formula = FormulaNode(signatures['Equals'], [a_node, b_node])
            equal_formulas.append(equal_formula)

        if not isinstance(a_sig, VariableSignature) or not isinstance(b_sig, VariableSignature):
            continue

        graph.add_edge(a_sig, b_sig)
        p = re.compile("^([A-Z]+|[a-z])$")
        if p.match(a_sig.name):
            explicit_sigs.add(a_sig)
        if p.match(b_sig.name):
            explicit_sigs.add(b_sig)

    tester = lambda sig: sig in graph and any(nx.has_path(graph, sig, explicit_sig) for explicit_sig in explicit_sigs)
    getter = lambda sig: [explicit_sig for explicit_sig in explicit_sigs if nx.has_path(graph, sig, explicit_sig)][0]
    new_formula_nodes = [formula_node.replace_signature(tester, getter) for formula_node in core_formulas]
    new_formula_nodes = new_formula_nodes + equal_formulas
    return new_formula_nodes

def _apply_cc(cc_formulas, core_formulas):
    graph = nx.Graph()
    firsts = set()
    for formula_node in cc_formulas:
        a_node, b_node = formula_node.children
        a_sig, b_sig = a_node.signature, b_node.signature
        firsts.add(a_sig)
        firsts.add(b_sig)
        graph.add_edge(a_sig, b_sig)

    def tester(node):
        if node.signature.valence == 2 and node.is_singular():
            child_node = node.children[0]
            if child_node.signature in graph.nodes() and len(graph.edges(child_node.signature)) == 1:
                nbr = graph[child_node.signature].keys()[0]
                if is_valid_relation(node.signature, nbr, 1):
                    nbr_node = FormulaNode(nbr, [])
                    return FormulaNode(node.signature, [node.children[0], nbr_node])

            # insert dummy variable
            nbr = VariableSignature("dummy", node.signature.arg_types[1], name=node.signature.arg_types[1])
            nbr_node = FormulaNode(nbr, [])
            return FormulaNode(node.signature, [node.children[0], nbr_node])

        if node.signature not in firsts:
            return None
        if node.parent is None:
            raise Exception
        if isinstance(node.parent, FormulaNode) and (node.parent.signature.valence == 1 or node.parent.is_plural()):
            args =  [FormulaNode(nbr, []) for nbr in graph[node.signature]
                     if is_valid_relation(node.parent.signature, nbr, node.index)]
            if len(args) == 0:
                return None
            return SetNode([node] + args)
        return None

    new_formula_nodes = [formula_node.replace_node(tester) for formula_node in core_formulas]
    return new_formula_nodes


def is_valid_relation(parent_signature, child_signature, index):
    parent_type = parent_signature.arg_types[index]
    child_type = child_signature.return_type
    if parent_type[0] != "*" and child_type == "*":
        return False
    if parent_type[0] == "*":
        parent_type = parent_type[1:]
    if child_type[0] == "*":
        child_type = child_type[1:]
    return issubtype(child_type, parent_type)

def filter_dummies(formula_nodes):
    """
    Remove (filter) formula nodes that were used to determine variable types
    e.g. IsLine, IsCircle, IsQuad, IsTriangle, etc.
    :param formula_nodes:
    :return:
    """
    dummies = ['IsLine', 'IsCircle', 'IsTriangle', 'IsQuad', 'IsAngle']
    new_nodes = []
    for formula_node in formula_nodes:
        if not formula_node.signature.id in dummies:
            new_nodes.append(formula_node)
    return new_nodes

def _apply_distribution(nodes):
    """
    If unary: just expand!
    If binary and same length: respectively
    if binary and one vs multi: expand for all
    use tester/getter to achieve this.

    :param formula_nodes:
    :return:
    """
    return [_apply_distribution_helper(node) for node in nodes]

def _apply_distribution_helper(node):
    if not isinstance(node, FormulaNode) or len(node.children) == 0:
        return node
    node = FormulaNode(node.signature, [_apply_distribution_helper(child) for child in node.children])
    if len(node.children) == 1:
        child_node = node.children[0]
        if isinstance(child_node, SetNode) and node.signature.arg_types[0][0] != '*':
            children = [FormulaNode(node.signature, [child]) for child in child_node.children]
            return SetNode(children)
    elif len(node.children) == 2:
        a_node, b_node = node.children
        if isinstance(a_node, SetNode) and node.signature.arg_types[0][0] != '*' and isinstance(b_node, SetNode) and node.signature.arg_types[1][0] != '*':
            assert len(a_node.children) == len(b_node.children)
            children = [FormulaNode(node.signature, [a_node.children[index], b_node.children[index]]) for index in range(len(a_node.children))]
            return SetNode(children)
        elif isinstance(a_node, SetNode) and node.signature.arg_types[0][0] != '*' and isinstance(b_node, FormulaNode):
            children = [FormulaNode(node.signature, [child, b_node]) for child in a_node.children]
            return SetNode(children)
        elif isinstance(a_node, FormulaNode) and isinstance(b_node, SetNode) and node.signature.arg_types[1][0] != '*':
            children = [FormulaNode(node.signature, [a_node, child]) for child in b_node.children]
            return SetNode(children)

    return node




