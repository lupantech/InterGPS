from collections import namedtuple
import itertools
import sympy
from geosolver.diagram.get_instances import get_all_instances, get_instances
from geosolver.geowordnet.identify_constants import _get_number_score, _get_variable_score
from geosolver.grounding.states import MatchParse, GroundedSemanticTree
from geosolver.ontology.instantiator_definitions import instantiators
from geosolver.ontology.states import Formula, Constant, Function
from geosolver.text.semantics.states import SemanticTree

__author__ = 'minjoon'

def ground_semantic_tree(match_parse, semantic_tree):
    """

    :param MatchParse match_parse:
    :param SemanticTree semantic_tree:
    :return tuple:
    """
    assert isinstance(semantic_tree, SemanticTree)
    assert isinstance(match_parse, MatchParse)
    text_formula = semantic_tree.formula
    grounded_semantic_trees = []
    packs = _ground_formula(match_parse, text_formula)
    for new_formula, variables, cost in packs:
        grounded_semantic_tree = GroundedSemanticTree(semantic_tree, new_formula, cost, variables)
        grounded_semantic_trees.append(grounded_semantic_tree)
    return grounded_semantic_trees

FormulaPack = namedtuple("FormulaPack", "formula variables cost")

def _ground_formula(match_parse, text_formula):
    """
    Helper function for ground_semantic_tree

    returns a tuple (grounded_formula, variables, cost)
    :param match_parse:
    :param formula:
    :return:
    """
    basic_ontology = text_formula.basic_ontolgy

    # Base cases: entity | number and constant | function | error
    current = text_formula.current  # current is either Constant or FormulaNode
    packs = []
    if isinstance(current, Constant) and basic_ontology.isinstance(current.type, basic_ontology.types['number']):
        # Either variable ('x', 'y', etc) or number ('1', '555', etc.)
        assert isinstance(current.content, str)
        number_cost = 1 - _get_number_score(current.content)
        variable_cost = 1 - _get_variable_score(current.content)
        if number_cost < 1:
            new_current = Constant(float(current.content), basic_ontology.types['number'])
            grounded_formula = Formula(basic_ontology, new_current, [])
            packs.append(FormulaPack(grounded_formula, {}, number_cost))

        if variable_cost < 1:
            variable = sympy.symbols(current.content)
            variables = {current.content: variable}
            new_current = Constant(variable, basic_ontology.types['number'])
            grounded_formula = Formula(basic_ontology, new_current, [])
            packs.append(FormulaPack(grounded_formula, variables, variable_cost))

    elif basic_ontology.isinstance(current.type, basic_ontology.types['entity']):
        # only single child
        packs.extend(_ground_entity(match_parse, text_formula))

    elif isinstance(current, Function):
        # Recursive case
        pack_list_of_list = [_ground_formula(match_parse, child) for child in text_formula.children]
        for pack_list in itertools.product(*pack_list_of_list):
            variables = {}
            cost = 0
            children = []
            for child, local_variables, local_cost in pack_list:
                children.append(child)
                cost += local_cost
                for key, value in local_variables.iteritems():
                    variables[key] = value
            grounded_formula = Formula(basic_ontology, current, children)
            packs.append(FormulaPack(grounded_formula, variables, cost))

    else:
        raise Exception("Something is wrong...")

    return packs


def _ground_entity(match_parse, entity_formula):
    """

    :param match_parse:
    :param entity_formula:
    :return:
    """
    assert isinstance(entity_formula, Formula)
    basic_ontology = entity_formula.basic_ontolgy
    current = entity_formula.current
    packs = []
    if isinstance(current, Constant):
        assert isinstance(current.content, tuple)
        packs.extend(_get_all(match_parse, basic_ontology, current.type))
    elif isinstance(current, Function):
        assert len(entity_formula.children) == 1
        child = entity_formula.children[0]
        assert isinstance(child.current, Constant)
        if isinstance(child.current.content, tuple):
            """
            child.current is an implied constant (content is a tuple referring to its parent)
            """
            packs.extend(_get_all(match_parse, basic_ontology, current.type))
        elif isinstance(child.current.content, str):
            """
            Get specific entities
            1. line AB, line CDE
            2. circle O
            3. arc AB
            4. triangle ABC
            5. plural returns all
            to be added further
            """
            # TODO : next thing to do! take a look at run_diagram's match parse and see how to use label
            packs.extend(_get_specific(match_parse, basic_ontology, current.type, child.current))

    return packs


def _get_all(match_parse, basic_ontology, type_):
    assert isinstance(match_parse, MatchParse)
    general_graph_parse = match_parse.general_graph_parse
    instances = get_all_instances(general_graph_parse, type_.name)
    assert isinstance(instances, dict)
    packs = []
    for key, d in instances.iteritems():
        instance = d['instance']
        constant = Constant(instance, type_)
        formula = Formula(basic_ontology, constant, [])
        variables = {}
        cost = 0
        packs.append(FormulaPack(formula, variables, cost))
    return packs


def _get_specific(match_parse, basic_ontology, type_, constant):
    assert isinstance(match_parse, MatchParse)
    assert isinstance(constant, Constant)
    packs = []
    if type_.name == 'line':
        label_a = constant.content[0]
        label_b = constant.content[-1]
        keys_a = match_parse.match_graph[label_a].keys()
        keys_b = match_parse.match_graph[label_b].keys()
        for key_a, key_b in itertools.product(keys_a, keys_b):
            point_a = match_parse.formulas[key_a]
            point_b = match_parse.formulas[key_b]

            if not isinstance(point_a, instantiators['point']) or not isinstance(point_b, instantiators['point']):
                continue

            a_key = _get_point_key(match_parse, point_a)
            b_key = _get_point_key(match_parse, point_b)
            lines = get_instances(match_parse.general_graph_parse, 'line', a_key, b_key).values()
            for line in lines:
                constant = Constant(line, basic_ontology.types['line'])
                formula = Formula(basic_ontology, constant, [])
                variables = {}
                cost = 0
                packs.append(FormulaPack(formula, variables, cost))

    elif type_.name == 'circle':
        if len(constant.content) == 1:
            label = constant.content[0]
            keys = match_parse.match_graph[label].keys()
            for key in keys:
                point = match_parse.formulas[key]

                if not isinstance(point, instantiators['point']):
                    continue

                key = _get_point_key(match_parse, point)
                circles = get_instances(match_parse.general_graph_parse, 'circle', key).values()
                for circle in circles:
                    constant = Constant(circle, basic_ontology.types['circle'])
                    formula = Formula(basic_ontology, constant, [])
                    variables = {}
                    cost = 0
                    packs.append(FormulaPack(formula, variables, cost))

    # TODO : Add other things as well

    return packs




def _get_point_key(match_parse, point):
    """
    Obtain the key for the point via reverse engineering

    :param match_parse:
    :param point:
    :return:
    """
    _, key_string, _ = str(point.x).split('_')
    key = int(key_string)
    return key
