"""
Matching is aligning labels and objects in diagram given entity formulas.
This package also provides mapping from text formula to diagram formula.


at the end, we just want string mapping to formula (one can maps to multiple,
so use graph)

"""
from geosolver.diagram.states import GraphParse

__author__ = 'minjoon'


class MatchNetwork(object):
    pass


class GroundedSemanticTree(object):
    def __init__(self, semantic_tree, grounded_formula, cost, variables):
        self.semantic_tree = semantic_tree
        self.grounded_formula = grounded_formula
        self.cost = cost
        self.variables = variables

class MatchParse(object):
    def __init__(self, graph_parse, match_dict, point_key_dict):
        assert isinstance(graph_parse, GraphParse)
        self.graph_parse = graph_parse
        self.match_dict = match_dict
        self.point_key_dict = point_key_dict

