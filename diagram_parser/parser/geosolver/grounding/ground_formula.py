import itertools
import logging
from geosolver.diagram.get_instances import get_all_instances, get_instances
from geosolver.grounding.states import MatchParse
from geosolver.ontology.ontology_semantics import evaluate, MeasureOf, IsHypotenuseOf
from geosolver.ontology.ontology_definitions import VariableSignature, signatures, FormulaNode, SetNode, is_singular, Node
from geosolver.utils.num import is_number
import numpy as np

__author__ = 'minjoon'


def ground_formulas(match_parse, formulas, references={}):
    core_parse = match_parse.graph_parse.core_parse
    singular_variables = set(itertools.chain(*[_get_singular_variables(formula) for formula in formulas]))
    grounded_variable_sets = []
    for variable in singular_variables:
        grounded_variable = _ground_variable(match_parse, variable, references)
        if isinstance(grounded_variable, FormulaNode): grounded_variable_sets.append([grounded_variable])
        else: grounded_variable_sets.append(grounded_variable.children)
    scores = []
    grounded_formulas_list = []
    combinations = list(itertools.product(*grounded_variable_sets))
    for combination in combinations:
        grounded_formulas = _combination_to_grounded_formulas(match_parse, formulas, combination, singular_variables)
        local_scores = [core_parse.evaluate(f) for f in grounded_formulas]
        scores.append(sum(s.conf for s in local_scores if s is not None))
        grounded_formulas_list.append(grounded_formulas)
    max_score, max_gf = max(zip(scores, grounded_formulas_list), key=lambda pair: pair[0])
    return max_gf


def _combination_to_grounded_formulas(match_parse, formulas, combination, singular_variables):
    var_dict = {variable_node.signature: combination[idx]
                for idx, variable_node in enumerate(singular_variables)}
    grounded_formulas = []
    for formula in formulas:
        singular_grounded_formula = _assign_variables(formula, var_dict)
        try:
            plural_grounded_formula = _ground_formula(match_parse, singular_grounded_formula)
            grounded_formula = _apply_distribution(plural_grounded_formula)
            grounded_formulas.append(grounded_formula)
        except:
            pass
    return grounded_formulas


def _assign_variables(formula_node, var_dict):
    tester = lambda node: isinstance(node, FormulaNode) and node.is_leaf() and node.signature in var_dict
    getter = lambda node: var_dict[node.signature]
    if not isinstance(formula_node, FormulaNode):
        raise Exception("%s: %r" % (formula_node.__class__.__name__, formula_node))
    out_node = formula_node.replace_node(tester, getter)
    return out_node


def _ground_formula(match_parse, formula, threshold=0.5):
    if formula.is_leaf():
        if formula.is_grounded(match_parse.graph_parse.core_parse.variable_assignment.keys()):
            out = formula
        else:
            out = _ground_variable(match_parse, formula)
    else:
        children = [_ground_formula(match_parse, child) for child in formula.children]
        if isinstance(formula, SetNode):
            if False: #formula.children[0].signature.return_type == 'truth':
                new_children = []
                for child in children:
                    if child.has_constant():
                        new_children.append(child)
                    else:
                        tv = match_parse.graph_parse.core_parse.evaluate(child)
                        if tv.conf > threshold:
                            new_children.append(child)
                out = SetNode(new_children)
            else:
                out = SetNode(children)
        else:
            out = FormulaNode(formula.signature, children)
    final = _apply_distribution(out)
    return final


def _get_singular_variables(formula_node):
    singular_variables = []
    for each_node in formula_node:
        if isinstance(each_node, FormulaNode) and each_node.is_leaf() and \
                isinstance(each_node.signature, VariableSignature) and not each_node.signature.name.endswith('s'):#is_singular(each_node.signature.return_type):
            singular_variables.append(each_node)
    return singular_variables


def _apply_distribution(node):
    if not isinstance(node, FormulaNode) or len(node.children) == 0:
        return node
    node = FormulaNode(node.signature, [_apply_distribution(child) for child in node.children])
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


def _ground_variable(match_parse, variable, references={}):
    assert isinstance(variable, FormulaNode)
    assert isinstance(match_parse, MatchParse)
    return_type = variable.return_type
    graph_parse = match_parse.graph_parse
    core_parse = graph_parse.core_parse
    variable_signature = variable.signature

    if variable_signature.id in signatures:
        # pass What, Which, etc.
        return variable
    elif variable_signature.id in match_parse.graph_parse.core_parse.variable_assignment.keys():
        # pass point_0, point_1, etc.
        return variable
    elif isinstance(variable_signature, VariableSignature) and variable_signature.is_ref():
        # @v_1, etc.
        return references[variable_signature.name]
    elif return_type == 'number':
        if is_number(variable_signature.name):
            return variable
        elif len(variable_signature.name) == 1:
            # x, y, z, etc. Need to redefine id (id shouldn't be tuple).
            return FormulaNode(VariableSignature(variable_signature.name, return_type), [])
        elif len(variable_signature.name) == 2 and variable_signature.name.isupper():
            new_leaf = FormulaNode(VariableSignature(variable.signature.id, "line", name=variable.signature.name), [])
            return FormulaNode(signatures['LengthOf'], [_ground_variable(match_parse, new_leaf)])
        else:
            # ABC: number -> just variable
            return variable
    elif return_type == 'point':
        if len(variable_signature.name) == 1:
            return match_parse.match_dict[variable_signature.name][0]
        else:
            points = get_all_instances(graph_parse, 'point', True)
            return SetNode(points.values())
    elif return_type == 'line':
        if len(variable_signature.name) == 1 and variable_signature.name in match_parse.match_dict:
            line = match_parse.match_dict[variable_signature.name][0]
            return line
        elif len(variable_signature.name) == 2 and variable_signature.name.isupper():
            label_a, label_b = variable_signature.name
            point_a = match_parse.match_dict[label_a][0]
            point_b = match_parse.match_dict[label_b][0]
            return FormulaNode(signatures['Line'], [point_a, point_b])
        else:
            lines = get_all_instances(graph_parse, 'line', True)
            return SetNode(lines.values())
    elif return_type == 'circle':
        if len(variable_signature.name) == 1:
            center_label = variable_signature.name
            center = match_parse.match_dict[center_label][0]
            center_idx = int(center.signature.name.split("_")[1])
            return graph_parse.circle_dict[center_idx][0]['variable']
            # radius = match_parse.graph_parse.core_parse.radius_variables[center_idx][0]
        elif variable_signature.name == 'circle':
            circles = get_all_instances(graph_parse, 'circle', True)
            return SetNode(circles.values())
        else:
            raise Exception()
    elif return_type == 'angle':
        # TODO :
        if len(variable_signature.name) == 3 and variable_signature.name.isupper():
            label_a, label_b, label_c = variable_signature.name
            point_a = match_parse.match_dict[label_a][0]
            point_b = match_parse.match_dict[label_b][0]
            point_c = match_parse.match_dict[label_c][0]
            out = FormulaNode(signatures['Angle'], [point_a, point_b, point_c])
            measure = evaluate(FormulaNode(signatures['MeasureOf'], [out]), core_parse.variable_assignment)
            if measure > np.pi:
                out = FormulaNode(signatures['Angle'], [point_c, point_b, point_a])
            return out
        elif len(variable_signature.name) == 1 and variable_signature.name.isupper():
            angles = get_all_instances(graph_parse, 'angle', True)
            p = match_parse.match_dict[variable_signature.name][0]
            for formula in angles.values():
                if formula.children[1].signature == p.signature:
                    measure = evaluate(FormulaNode(signatures['MeasureOf'], [formula]), core_parse.variable_assignment)
                    if measure > np.pi:
                        continue
                    return formula
        elif len(variable_signature.name) == 1 and variable_signature.name.islower() and variable_signature.name in match_parse.match_dict:
            return match_parse.match_dict[variable_signature.name][0]
        else:
            angles = get_all_instances(graph_parse, 'angle', True)
            return SetNode(angles.values())
    elif return_type == 'arc':
        if len(variable_signature.name) == 2 and variable_signature.name.isupper():
            point_keys = [match_parse.point_key_dict[label] for label in variable_signature.name]
            test_arc = get_instances(graph_parse, 'arc', False, *point_keys).values()[0]
            if MeasureOf(test_arc) > np.pi:
                point_keys = [point_keys[1], point_keys[0]]
            arc = get_instances(graph_parse, 'arc', True, *point_keys).values()[0]
            return arc
        else:
            arcs = get_all_instances(graph_parse, 'arc', True)
            return SetNode(arcs.values())

    elif return_type == 'triangle':
        if variable_signature.name.isupper() and len(variable_signature.name) == 3:
            point_keys = [match_parse.point_key_dict[label] for label in variable_signature.name]
            triangles = get_instances(graph_parse, 'triangle', True, *point_keys)
            return triangles.values()[0]
        else:
            triangles = get_all_instances(graph_parse, 'triangle', True)
            return SetNode(triangles.values())
    elif return_type == 'quad':
        if variable_signature.name.isupper() and len(variable_signature.name) == 4:
            point_keys = [match_parse.point_key_dict[label] for label in variable_signature.name]
            quads = get_instances(graph_parse, 'quad', True, *point_keys)
            return quads.values()[0]
        else:
            quads = get_all_instances(graph_parse, 'quad', True)
            return SetNode(quads.values())
    elif return_type == 'hexagon':
        if variable_signature.name.isupper() and len(variable_signature.name) == 6:
            point_keys = [match_parse.point_key_dict[label] for label in variable_signature.name]
            hexagons = get_instances(graph_parse, 'hexagon', True, *point_keys)
            return hexagons.values()[0]
        else:
            quads = get_all_instances(graph_parse, 'hexagon', True)
            return SetNode(quads.values())
    elif return_type == 'polygon':
        if variable_signature.name.isupper():
            point_keys = [match_parse.point_key_dict[label] for label in variable_signature.name]
            polygons = get_instances(graph_parse, 'polygon', True, *point_keys)
            return polygons.values()[0]
        else:
            polygons = get_all_instances(graph_parse, 'polygon', True)
            return SetNode(polygons.values())
    elif return_type == 'twod':
        circles = get_all_instances(graph_parse, 'circle', True)
        polygons = get_all_instances(graph_parse, 'polygon', True)
        return SetNode(polygons.values() + circles.values())
    elif return_type == 'oned':
        lines = get_all_instances(graph_parse, 'line', True)
        arcs = get_all_instances(graph_parse, 'arc', True)
        return SetNode(lines.values() + arcs.values())

    logging.error("failed to ground variable: %r" % variable)
    return variable
