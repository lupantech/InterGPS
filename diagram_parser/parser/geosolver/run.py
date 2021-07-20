from cStringIO import StringIO
import json
import logging
import numbers
from pprint import pprint
import shutil
import sys
import time
import signal
from geosolver import geoserver_interface
from geosolver.database.utils import split
from geosolver.diagram.parse_confident_formulas import parse_confident_formulas
from geosolver.diagram.shortcuts import question_to_match_parse
from geosolver.expression.expression_parser import expression_parser
from geosolver.expression.prefix_to_formula import prefix_to_formula
from geosolver.grounding.ground_formula import ground_formulas
from geosolver.grounding.parse_match_formulas import parse_match_formulas
from geosolver.grounding.parse_match_from_known_labels import parse_match_from_known_labels
from geosolver.ontology.ontology_definitions import FormulaNode, VariableSignature, issubtype
from geosolver.ontology.ontology_semantics import evaluate, Equals
from geosolver.solver.solve import solve
from geosolver.text.augment_formulas import augment_formulas
from geosolver.text.opt_model import TextGreedyOptModel, GreedyOptModel, FullGreedyOptModel
from geosolver.text.rule import TagRule
from geosolver.text.rule_model import CombinedModel
from geosolver.text.run_text import train_semantic_model, questions_to_syntax_parses, train_tag_model
from geosolver.text.semantic_tree import SemanticTreeNode
from geosolver.text.semantic_trees_to_text_formula_parse import semantic_trees_to_text_formula_parse
from geosolver.text.annotation_to_semantic_tree import annotation_to_semantic_tree, is_valid_annotation
from geosolver.text.complete_formulas import complete_formulas
from geosolver.text.syntax_parser import stanford_parser
from geosolver.ontology.utils import filter_formulas, reduce_formulas
from geosolver.ontology.utils import flatten_formulas
from geosolver.utils.prep import open_image
import cPickle as pickle
import os.path

__author__ = 'minjoon'
from json import encoder
encoder.FLOAT_REPR = lambda o: format(o, '.2f')

class SimpleResult(object):
    def __init__(self, id_, error, penalized, correct, duration=-1, message=""):
        assert isinstance(penalized, bool)
        assert isinstance(correct, bool)
        assert isinstance(error, bool)
        assert isinstance(duration, numbers.Real)
        assert isinstance(message, str)
        self.id = id_
        self.penalized = penalized
        self.correct = correct
        self.duration = duration
        self.message = message
        self.error = error

    def __repr__(self):
        return "(e,p,c) = %s, %s, %s" % (self.error, self.penalized, self.correct)

def annotated_unit_test(query):
    """
    Attempts to solve the question with id=id_.
    If the answer is correct, return 'c'
    If the answer is wrong, return 'i'
    If an error occurred, return 'e'

    :param id_:
    :return SimpleResult:
    """
    #myout = StringIO()
    #oldstdout = sys.stdout
    #sys.stdout = myout

    try:
        result = _annotated_unit_test(query)
    except Exception, e:
        logging.error(query)
        logging.exception(e)
        result = SimpleResult(query, True, False, False)
    #sys.stdout = oldstdout
    #message = myout.getvalue()
    #result.message = message
    return result

def _annotated_unit_test(query):
    questions = geoserver_interface.download_questions(query)
    all_annotations = geoserver_interface.download_semantics(query)
    pk, question = questions.items()[0]

    choice_formulas = get_choice_formulas(question)
    label_data = geoserver_interface.download_labels(pk)[pk]
    diagram = open_image(question.diagram_path)
    graph_parse = diagram_to_graph_parse(diagram)
    core_parse = graph_parse.core_parse
    # core_parse.display_points()
    # core_parse.primitive_parse.display_primitives()
    match_parse = parse_match_from_known_labels(graph_parse, label_data)
    match_formulas = parse_match_formulas(match_parse)
    diagram_formulas = parse_confident_formulas(graph_parse)
    all_formulas = match_formulas + diagram_formulas
    for number, sentence_words in question.sentence_words.iteritems():
        syntax_parse = stanford_parser.get_best_syntax_parse(sentence_words)
        annotation_nodes = [annotation_to_semantic_tree(syntax_parse, annotation)
                            for annotation in all_annotations[pk][number].values()]
        expr_formulas = {key: prefix_to_formula(expression_parser.parse_prefix(expression))
                         for key, expression in question.sentence_expressions[number].iteritems()}
        truth_expr_formulas, value_expr_formulas = _separate_expr_formulas(expr_formulas)
        text_formula_parse = semantic_trees_to_text_formula_parse(annotation_nodes)
        completed_formulas = complete_formulas(text_formula_parse)
        grounded_formulas = [ground_formula(match_parse, formula, value_expr_formulas)
                             for formula in completed_formulas+truth_expr_formulas]
        text_formulas = filter_formulas(flatten_formulas(grounded_formulas))
        all_formulas.extend(text_formulas)

    reduced_formulas = reduce_formulas(all_formulas)
    for reduced_formula in reduced_formulas:
        score = evaluate(reduced_formula, core_parse.variable_assignment)
        scores = [evaluate(child, core_parse.variable_assignment) for child in reduced_formula.children]
        print reduced_formula, score, scores
    # core_parse.display_points()

    ans = solve(reduced_formulas, choice_formulas, assignment=core_parse.variable_assignment)
    print "ans:", ans

    if choice_formulas is None:
        attempted = True
        if abs(ans - float(question.answer)) < 0.01:
            correct = True
        else:
            correct = False
    else:
        attempted = True
        c = max(ans.iteritems(), key=lambda pair: pair[1].conf)[0]
        if c == int(float(question.answer)):
            correct = True
        else:
            correct = False

    result = SimpleResult(query, False, attempted, correct)
    return result

def full_unit_test(combined_model, question, label_data):
    """
    Attempts to solve the question with id=id_.
    If the answer is correct, return 'c'
    If the answer is wrong, return 'i'
    If an error occurred, return 'e'

    :param id_:
    :return SimpleResult:
    """
    maxtime = 2400

    def handler(signum, frame):
        raise Exception("Timeout")
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(maxtime)

    try:
        result = _full_unit_test(combined_model, question, label_data)
    except Exception, e:
        logging.error(question.key)
        logging.exception(e)
        result = SimpleResult(question.key, True, False, False)
    #sys.stdout = oldstdout
    #message = myout.getvalue()
    #result.message = message
    return result

    # graph_parse.core_parse.display_points()

def semantic_tree_to_serialized_entities(match_parse, semantic_tree, sentence_number, value_expr_formulas):
    offset = match_parse.graph_parse.core_parse.image_segment_parse.diagram_image_segment.offset
    formula = semantic_tree.to_formula()
    entities = []
    grounded_formula = ground_formulas(match_parse, [formula], value_expr_formulas)[0]
    zipped_formula = grounded_formula.zip(semantic_tree)
    for zipped_node in zipped_formula:
        formula_node, tree_node = zipped_node.nodes
        if isinstance(formula_node, FormulaNode) and issubtype(formula_node.return_type, 'entity'):
            coords = match_parse.graph_parse.core_parse.evaluate(formula_node)
            if coords is not None:
                coords = offset_coords(coords, tree_node.content.signature.return_type, offset)
                entity = {"content": tree_node.content.serialized(), "coords": serialize_entity(coords),
                          "sentence_number": sentence_number}
                entities.append(entity)
    return entities

def formula_to_serialized_entities(match_parse, formula, tree, sentence_number):
    offset = match_parse.graph_parse.core_parse.image_segment_parse.diagram_image_segment.offset
    grounded_formula = ground_formulas(match_parse, [formula])[0]
    entities = []
    zipped_formula = grounded_formula.zip(tree)
    for zipped_node in zipped_formula:
        formula_node, tree_node = zipped_node.nodes
        if not isinstance(formula_node, FormulaNode):
            continue
        if len(formula_node.children) == 1 and not issubtype(formula_node.return_type, 'entity'):
            formula_node = formula_node.children[0]
        if issubtype(formula_node.return_type, 'entity'):
            coords = match_parse.graph_parse.core_parse.evaluate(formula_node)
            if coords is not None:
                coords = offset_coords(coords, formula_node.return_type, offset)
                content = tree_node.content.serialized()
                content['signature']['return_type'] = formula_node.return_type
                entity = {"content": content, "coords": serialize_entity(coords),
                          "sentence_number": sentence_number}
                entities.append(entity)
    return entities

def offset_point(point, offset):
    return point[0]+offset[0], point[1]+offset[1]

def offset_coords(coords, type_, offset):
    coords = list(coords)
    if issubtype(type_, 'point'):
        coords = offset_point(coords, offset)
    elif issubtype(type_, "line"):
        coords[0] = offset_point(coords[0], offset)
        coords[1] = offset_point(coords[1], offset)
    elif issubtype(type_, 'circle'):
        coords[0] = offset_point(coords[0], offset)
    elif issubtype(type_, 'arc') or issubtype(type_, 'sector'):
        coords[0][0] = offset_point(coords[0][0], offset)
        coords[1] = offset_point(coords[1], offset)
        coords[2] = offset_point(coords[2], offset)
    else:
        coords = [offset_point(point, offset) for point in coords]
    return coords


def serialize_entity(entity):
    try:
        return [serialize_entity(each) for each in entity]
    except:
        return float("%.2f" % entity)

def formula_to_semantic_tree(formula, syntax_parse, span):
    """
    Create dummy semantic tree where each tag's syntax Parse and span is given
    :param formula:
    :param index:
    :return:
    """
    assert isinstance(formula, FormulaNode)
    if issubtype(formula.signature.return_type, 'entity'):
        new_sig = VariableSignature(formula.signature.id, formula.signature.return_type, name='temp')
        tag_rule = TagRule(syntax_parse, span, new_sig)
        return SemanticTreeNode(tag_rule, [])
    tag_rule = TagRule(syntax_parse, span, formula.signature)
    children = [formula_to_semantic_tree(child, syntax_parse, span) for child in formula.children]
    semantic_tree = SemanticTreeNode(tag_rule, children)
    return semantic_tree


demo_path = "../temp/demo"

def _full_unit_test(combined_model, question, label_data):
    assert isinstance(combined_model, CombinedModel)

    base_path = os.path.join(demo_path, str(question.key))
    if not os.path.exists(base_path):
        os.mkdir(base_path)
    question_path = os.path.join(base_path, 'question.json')
    text_parse_path = os.path.join(base_path, 'text_parse.json')
    diagram_parse_path = os.path.join(base_path, 'diagram_parse.json')
    optimized_path = os.path.join(base_path, 'optimized.json')
    entity_list_path = os.path.join(base_path, 'entity_map.json')
    diagram_path = os.path.join(base_path, 'diagram.png')
    solution_path = os.path.join(base_path, 'solution.json')
    shutil.copy(question.diagram_path, diagram_path)
    text_parse_list = []
    diagram_parse_list = []
    optimized_list = []
    entity_list = []
    solution = ""
    json.dump(question._asdict(), open(question_path, 'wb'))

    choice_formulas = get_choice_formulas(question)
    match_parse = question_to_match_parse(question, label_data)
    match_formulas = parse_match_formulas(match_parse)
    graph_parse = match_parse.graph_parse
    core_parse = graph_parse.core_parse
    # core_parse.display_points()
    # core_parse.primitive_parse.display_primitives()

    # opt_model = TextGreedyOptModel(combined_model)

    diagram_formulas = parse_confident_formulas(match_parse.graph_parse)
    all_formulas = set(match_formulas + diagram_formulas)

    opt_model = FullGreedyOptModel(combined_model, match_parse)
    for number, sentence_words in question.sentence_words.iteritems():
        syntax_parse = stanford_parser.get_best_syntax_parse(sentence_words)

        expr_formulas = {key: prefix_to_formula(expression_parser.parse_prefix(expression))
                         for key, expression in question.sentence_expressions[number].iteritems()}
        truth_expr_formulas, value_expr_formulas = _separate_expr_formulas(expr_formulas)

        semantic_forest = opt_model.combined_model.get_semantic_forest(syntax_parse)
        truth_semantic_trees = semantic_forest.get_semantic_trees_by_type("truth")
        is_semantic_trees = semantic_forest.get_semantic_trees_by_type("is")
        cc_trees = set(t for t in semantic_forest.get_semantic_trees_by_type('cc')
                       if opt_model.combined_model.get_tree_score(t) > 0.01)
        for cc_tree in cc_trees:
            print "cc tree:", cc_tree, opt_model.combined_model.get_tree_score(cc_tree)

        bool_semantic_trees = opt_model.optimize(truth_semantic_trees.union(is_semantic_trees), 0, cc_trees)
        # semantic_trees = bool_semantic_trees.union(cc_trees)

        for t in truth_semantic_trees.union(is_semantic_trees).union(cc_trees):
            text_parse_list.append({'simple': t.simple_repr(), 'tree': t.serialized(), 'sentence_number': number,
                                    'score': opt_model.combined_model.get_tree_score(t)})
            diagram_score = opt_model.get_diagram_score(t.to_formula(), cc_trees)
            if diagram_score is not None:
                diagram_parse_list.append({'simple': t.simple_repr(), 'tree': t.serialized(), 'sentence_number': number,
                                           'score': diagram_score})

            local_entities = semantic_tree_to_serialized_entities(match_parse, t, number, value_expr_formulas)
            entity_list.extend(local_entities)

        for t in bool_semantic_trees:
            optimized_list.append({'simple': t.simple_repr(), 'tree': t.serialized(), 'sentence_number': number,
                                    'score': opt_model.get_magic_score(t, cc_trees)})

        for key, f in expr_formulas.iteritems():
            if key.startswith("v"):
                pass
            index = (i for i, word in sentence_words.iteritems() if word == key).next()
            tree = formula_to_semantic_tree(f, syntax_parse, (index, index+1))
            print "f and t:", f, tree
            text_parse_list.append({'simple': f.simple_repr(), 'tree': tree.serialized(), 'sentence_number': number, 'score': 1.0})
            optimized_list.append({'simple': f.simple_repr(), 'tree': tree.serialized(), 'sentence_number': number, 'score': 1.0})

            local_entities = formula_to_serialized_entities(match_parse, f, tree, number)
            print "local entities:", local_entities
            entity_list.extend(local_entities)



        core_formulas = set(t.to_formula() for t in bool_semantic_trees)
        cc_formulas = set(t.to_formula() for t in cc_trees)
        augmented_formulas = augment_formulas(core_formulas)
        completed_formulas = complete_formulas(augmented_formulas, cc_formulas)

        print "completed formulas:"
        for f in completed_formulas: print f
        print ""

        grounded_formulas = ground_formulas(match_parse, completed_formulas+truth_expr_formulas, value_expr_formulas)
        text_formulas = filter_formulas(flatten_formulas(grounded_formulas))
        all_formulas = all_formulas.union(text_formulas)

    reduced_formulas = all_formulas # reduce_formulas(all_formulas)
    for reduced_formula in reduced_formulas:
        if reduced_formula.is_grounded(core_parse.variable_assignment.keys()):
            score = evaluate(reduced_formula, core_parse.variable_assignment)
            scores = [evaluate(child, core_parse.variable_assignment) for child in reduced_formula.children]
        else:
            score = None
            scores = None
        solution += repr(reduced_formula) + '\n'
        print reduced_formula, score, scores
    solution = solution.rstrip()
    # core_parse.display_points()

    json.dump(diagram_parse_list, open(diagram_parse_path, 'wb'))
    json.dump(optimized_list, open(optimized_path, 'wb'))
    json.dump(text_parse_list, open(text_parse_path, 'wb'))
    json.dump(entity_list, open(entity_list_path, 'wb'))
    json.dump(solution, open(solution_path, 'wb'))

    # return SimpleResult(question.key, False, False, True) # Early termination

    print "Solving..."
    ans = solve(reduced_formulas, choice_formulas, assignment=None)#core_parse.variable_assignment)
    print "ans:", ans


    if choice_formulas is None:
        penalized = False
        if Equals(ans, float(question.answer)).conf > 0.98:
            correct = True
        else:
            correct = False
    else:
        idx, tv = max(ans.iteritems(), key=lambda pair: pair[1].conf)
        if tv.conf > 0.98:
            if idx == int(float(question.answer)):
                correct = True
                penalized = False
            else:
                correct = False
                penalized = True
        else:
            penalized = False
            correct = False

    result = SimpleResult(question.key, False, penalized, correct)
    return result

    # graph_parse.core_parse.display_points()

def _separate_expr_formulas(expr_formulas):
    truth_expr_formulas = []
    value_expr_formulas = {}
    for key, expr_formula in expr_formulas.iteritems():
        if key[1] == 's':
            truth_expr_formulas.append(expr_formula)
        else:
            value_expr_formulas[key] = expr_formula
    return truth_expr_formulas, value_expr_formulas

def get_choice_formulas(question):
    """
    Temporary; will be replaced by text parser
    :param question:
    :return:
    """
    choice_formulas = {}
    for number, choice_expressions in question.choice_expressions.iteritems():
        choice_words = question.choice_words[number]
        if len(choice_expressions) == 1:
            string = choice_expressions.values()[0]
        elif len(choice_expressions) == 0:
            if len(choice_words) == 1:
                string = choice_words.values()[0]
            else:
                continue
                # string = r"\none"
        else:
            return None
        expr_formula = prefix_to_formula(expression_parser.parse_prefix(string))
        choice_formulas[number] = expr_formula
    if len(choice_formulas) == 0:
        return None
    return choice_formulas


def annotated_test():
    ids1 = [963, 968, 969, 971, 973, 974, 977, 985, 990, 993, 995, 1000, 1003, 1004, 1006, 1011, 1014, 1017, 1018, 1020,]
    ids2 = [1025, 1030, 1031, 1032, 1035, 1037, 1038, 1039, 1040, 1042, 1043, 1045, 1047, 1050, 1051, 1052, 1054, 1056, 1058,] # 1027
    ids3 = [1063, 1065, 1067, 1076, 1089, 1095, 1096, 1097, 1099, 1102, 1105, 1106, 1107, 1108, 1110, 1111, 1119, 1120, 1121] # 1103
    ids4 = [1122, 1123, 1124, 1127, 1141, 1142, 1143, 1145, 1146, 1147, 1149, 1150, 1151, 1152, 1070, 1083, 1090, 1092, 1144, 1148]
    ids6 = [997, 1046, 1053]
    ids = ids1 + ids2 + ids3 + ids4 + ids5
    #ids = [973]
    correct = 0
    attempted = 0
    total = len(ids)
    error = 0
    start = time.time()
    for idx, id_ in enumerate(ids):
        print "-"*80
        print "%d/%d complete" % (idx+1, len(ids))
        id_ = str(id_)
        print "-"*80
        print "id: %s" % id_
        result = annotated_unit_test(id_)
        print result.message
        print result
        if result.error:
            error += 1
        if result.attempted:
            attempted += 1
        if result.correct:
            correct += 1
    end = time.time()
    print "-"*80
    print "duration:\t%.1f" % (end - start)

    out = "total:\t\t%d\nattempted:\t%d\ncorrect:\t%d\nerror:\t\t%d" % (total, attempted, correct, error)
    print out

def full_test():
    start = time.time()
    ids1 = [963, 968, 969, 971, 973, 974, 977, 985, 990, 993, 995, 1000, 1003, 1004, 1006, 1014, 1017, 1018, 1020,] #1011
    ids2 = [1025, 1030, 1031, 1032, 1035, 1038, 1039, 1040, 1042, 1043, 1045, 1047, 1050, 1051, 1052, 1054, 1056, 1058,] #1027, 1037
    ids3 = [1063, 1065, 1067, 1076, 1089, 1095, 1096, 1097, 1099, 1102, 1105, 1106, 1107, 1108, 1110, 1111, 1119, 1120, 1121] # 1103
    ids4 = [1122, 1123, 1124, 1127, 1141, 1142, 1143, 1145, 1146, 1147, 1149, 1150, 1151, 1152, 1070, 1083, 1090, 1092, 1144, 1148]
    ids5 = [975, 979, 981, 988, 989, 997, 1005, 1019, 1029, 1044, 1046, 1057, 1059, 1064, 1087, 1104, 1113, 1114, 1129, 1071]
    ids6 = [1100, 1101, 1109, 1140, 1053]
    tr_ids = ids4+ids5+ids6
    te_ids = ids1+ids2+ids3
    te_ids = ids4+ids6

    load = False

    tr_questions = geoserver_interface.download_questions('aaai')
    te_questions = geoserver_interface.download_questions('official')
    te_keys = te_questions.keys() # [968, 971, 973, 1018]
    all_questions = dict(tr_questions.items() + te_questions.items())
    tr_ids = tr_questions.keys()
    te_ids = te_questions.keys()

    if not load:
        all_syntax_parses = questions_to_syntax_parses(all_questions)
        pickle.dump(all_syntax_parses, open('syntax_parses.p', 'wb'))
    else:
        all_syntax_parses = pickle.load(open('syntax_parses.p', 'rb'))
    all_annotations = geoserver_interface.download_semantics()
    all_labels = geoserver_interface.download_labels()

    correct = 0
    penalized = 0
    error = 0
    total = len(te_keys)

    #(te_s, te_a, te_l), (tr_s, tr_a, trl_l) = split([all_syntax_parses, all_annotations, all_labels], 0.7)
    tr_s = {id_: all_syntax_parses[id_] for id_ in tr_ids}
    tr_a = {id_: all_annotations[id_] for id_ in tr_ids}
    te_s = {id_: all_syntax_parses[id_] for id_ in te_ids}

    if not load:
        tm = train_tag_model(all_syntax_parses, all_annotations)
        cm = train_semantic_model(tm, tr_s, tr_a)
        pickle.dump(cm, open('cm.p', 'wb'))
    else:
        cm = pickle.load(open('cm.p', 'rb'))

    print "test ids: %s" % ", ".join(str(k) for k in te_s.keys())
    for idx, id_ in enumerate(te_keys):
        question = all_questions[id_]
        label = all_labels[id_]
        id_ = str(id_)
        print "-"*80
        print "id: %s" % id_
        result = full_unit_test(cm, question, label)
        print result.message
        print result
        if result.error:
            error += 1
        if result.penalized:
            penalized += 1
        if result.correct:
            correct += 1
        print "-"*80
        print "%d/%d complete, %d correct, %d penalized, %d error" % (idx+1, len(te_keys), correct, penalized, error)
    end = time.time()
    print "-"*80
    print "duration:\t%.1f" % (end - start)

    out = "total:\t\t%d\npenalized:\t%d\ncorrect:\t%d\nerror:\t\t%d" % (total, penalized, correct, error)
    print out

    dirs_path = os.path.join(demo_path, 'dirs.json')
    json.dump([str(x) for x in te_keys], open(dirs_path, 'wb'))


def data_stat(query):
    questions = geoserver_interface.download_questions(query)
    syntax_parses = questions_to_syntax_parses(questions, parser=False)
    annotations = geoserver_interface.download_semantics(query)
    unary_rules = []
    binary_rules = []
    semantic_trees = []
    for pk, local_syntax_parses in syntax_parses.iteritems():
        print pk
        for number, syntax_parse in local_syntax_parses.iteritems():
            local_semantic_trees = [annotation_to_semantic_tree(syntax_parse, annotation)
                              for annotation in annotations[pk][number].values()]
            semantic_trees.extend(local_semantic_trees)
            print local_semantic_trees
            for semantic_tree in local_semantic_trees:
                unary_rules.extend(semantic_tree.get_unary_rules())
                binary_rules.extend(semantic_tree.get_binary_rules())

    tag_model = train_tag_model(syntax_parses, annotations)

    print "sentences: %d" % sum(len(question.sentence_words) for _, question in questions.iteritems())
    print "words: %d" % (sum(len(words) for _, question in questions.iteritems() for _, words in question.sentence_words.iteritems()))
    print "literals: %d" % len(semantic_trees)
    print "unary rules: %d" % len(unary_rules)
    print "binary rules: %d" % len(binary_rules)

    print ""
    print "LEXICON"
    for key, s in tag_model.lexicon.iteritems():
        print "%s: %s" % ("_".join(key), ", ".join(" ".join(ss) for ss in s))




if __name__ == "__main__":
    # annotated_test()
    full_test()
    # data_stat('emnlp')
