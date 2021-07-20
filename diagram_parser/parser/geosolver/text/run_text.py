from collections import defaultdict
import itertools

import numpy as np
import matplotlib.pyplot as plt
import time

from geosolver import geoserver_interface
from geosolver.database.utils import split
from geosolver.diagram.shortcuts import question_to_match_parse, questions_to_match_parses
from geosolver.ontology.ontology_definitions import VariableSignature
from geosolver.text.annotation_to_semantic_tree import annotation_to_semantic_tree
from geosolver.text.opt_model import GreedyOptModel, TextGreedyOptModel, FullGreedyOptModel
from geosolver.text.rule_model import NaiveTagModel, CombinedModel, \
    RFUnaryModel, RFCoreModel, RFIsModel, RFCCModel, filter_tag_rules, NaiveCCModel
from geosolver.text.semantic_forest import SemanticForest
from geosolver.text.syntax_parser import SyntaxParse, stanford_parser
import pickle as pickle

__author__ = 'minjoon'


def questions_to_syntax_parses(questions, parser=True):
    syntax_parses = {pk: {number: stanford_parser.get_best_syntax_parse(words, parser=parser)
                          for number, words in question.sentence_words.iteritems()}
                     for pk, question in questions.iteritems()}
    return syntax_parses


def split_binary_rules(binary_rules):
    core_rules = set()
    is_rules = set()
    cc_rules = set()
    for br in binary_rules:
        id_ = br.parent_tag_rule.signature.id
        if id_ == "Is":
            is_rules.add(br)
        elif id_ == "CC":
            cc_rules.add(br)
        else:
            core_rules.add(br)
    return core_rules, is_rules, cc_rules

def train_tag_model(syntax_parses, annotations):
    tm = NaiveTagModel()

    for pk, local_syntax_parses in syntax_parses.iteritems():
        for number, syntax_parse in local_syntax_parses.iteritems():
            semantic_trees = [annotation_to_semantic_tree(syntax_parse, annotation)
                              for annotation in annotations[pk][number].values()]
            assert isinstance(syntax_parse, SyntaxParse)
            local_tag_rules = set(itertools.chain(*[semantic_tree.get_tag_rules() for semantic_tree in semantic_trees]))
            tm.update(local_tag_rules)
    return tm

def train_semantic_model(tm, syntax_parses, annotations):
    um = RFUnaryModel()
    corem = RFCoreModel()
    ism = RFIsModel()
    ccm = NaiveCCModel(3)

    for pk, local_syntax_parses in syntax_parses.iteritems():
        print ("training:", pk)
        for number, syntax_parse in local_syntax_parses.iteritems():
            assert isinstance(syntax_parse, SyntaxParse)
            semantic_trees = [annotation_to_semantic_tree(syntax_parse, annotation)
                              for annotation in annotations[pk][number].values()]
            # local_tag_rules = set(itertools.chain(*[t.get_tag_rules() for t in semantic_trees]))
            local_tag_rules = tm.generate_tag_rules(syntax_parse)
            local_unary_rules = set(itertools.chain(*[semantic_tree.get_unary_rules() for semantic_tree in semantic_trees]))
            local_binary_rules = set(itertools.chain(*[semantic_tree.get_binary_rules() for semantic_tree in semantic_trees]))
            core_rules, is_rules, cc_rules = split_binary_rules(local_binary_rules)

            # Sanity check
            for ur in local_unary_rules:
                assert um.val_func(ur.parent_tag_rule, ur.child_tag_rule)
            for br in core_rules:
                assert corem.val_func(br.parent_tag_rule, br.child_a_tag_rule, br.child_b_tag_rule)

            um.update(local_tag_rules, local_unary_rules)
            corem.update(local_tag_rules, core_rules)
            ism.update(local_tag_rules, is_rules)
            #ccm.update(local_tag_rules, cc_rules)

    um.fit()
    corem.fit()
    ism.fit()
    #ccm.fit()

    cm = CombinedModel(tm, um, corem, ism, ccm)
    return cm





def evaluate_rule_model(combined_model, syntax_parses, annotations, thresholds):
    all_pos_unary_rules = []
    all_pos_core_rules = []
    all_pos_is_rules = []
    all_pos_cc_rules = []
    all_neg_unary_rules = []
    all_neg_core_rules = []
    all_neg_is_rules = []
    all_neg_cc_rules = []

    all_pos_bool_semantic_trees = []
    all_neg_bool_semantic_trees = []

    for pk, local_syntax_parses in syntax_parses.iteritems():
        print ("\n\n\n")
        print (pk)
        for number, syntax_parse in local_syntax_parses.iteritems():
            pos_semantic_trees = set(annotation_to_semantic_tree(syntax_parse, annotation)
                                     for annotation in annotations[pk][number].values())

            pos_unary_rules = set(itertools.chain(*[semantic_tree.get_unary_rules() for semantic_tree in pos_semantic_trees]))
            pos_binary_rules = set(itertools.chain(*[semantic_tree.get_binary_rules() for semantic_tree in pos_semantic_trees]))

            tag_rules = combined_model.tag_model.generate_tag_rules(syntax_parse)
            # tag_rules = set(itertools.chain(*[t.get_tag_rules() for t in pos_semantic_trees]))

            unary_rules = combined_model.generate_unary_rules(tag_rules)

            tag_rules = filter_tag_rules(combined_model.unary_model, tag_rules, unary_rules, 0.9)

            binary_rules = combined_model.generate_binary_rules(tag_rules)
            core_rules = combined_model.core_model.generate_binary_rules(tag_rules)
            is_rules = combined_model.is_model.generate_binary_rules(tag_rules)
            cc_rules = combined_model.cc_model.generate_binary_rules(tag_rules)
            pos_core_rules, pos_is_rules, pos_cc_rules = split_binary_rules(pos_binary_rules)
            span_pos_cc_rules = set(r.to_span_rule() for r in pos_cc_rules)
            negative_unary_rules = unary_rules - pos_unary_rules
            neg_core_rules = core_rules - pos_core_rules
            neg_is_rules = is_rules - pos_is_rules
            # neg_cc_rules = cc_rules - pos_cc_rules
            neg_cc_rules = set()
            pos_cc_rules = set()
            for r in cc_rules:
                if r.to_span_rule() in span_pos_cc_rules:
                    pos_cc_rules.add(r)
                else:
                    neg_cc_rules.add(r)

            all_pos_unary_rules.extend(pos_unary_rules)
            all_pos_core_rules.extend(pos_core_rules)
            all_pos_is_rules.extend(pos_is_rules)
            all_pos_cc_rules.extend(pos_cc_rules)
            all_neg_unary_rules.extend(negative_unary_rules)
            all_neg_core_rules.extend(neg_core_rules)
            all_neg_is_rules.extend(neg_is_rules)
            all_neg_cc_rules.extend(neg_cc_rules)

            pos_bool_semantic_trees = set(t for t in pos_semantic_trees if t.content.signature.id != 'CC')

            semantic_forest = SemanticForest(tag_rules, unary_rules, binary_rules)
            bool_semantic_trees = semantic_forest.get_semantic_trees_by_type("truth").union(semantic_forest.get_semantic_trees_by_type('is'))
            neg_bool_semantic_trees = bool_semantic_trees - pos_bool_semantic_trees
            all_pos_bool_semantic_trees.extend(pos_bool_semantic_trees)
            all_neg_bool_semantic_trees.extend(neg_bool_semantic_trees)

            for pst in pos_bool_semantic_trees:
                print ("pos:", combined_model.get_tree_score(pst), pst)
            print ("")
            for nst in neg_bool_semantic_trees:
                score = combined_model.get_tree_score(nst)
                if score > 0:
                    print ("neg:", combined_model.get_tree_score(nst), nst)

    unary_prs = combined_model.unary_model.get_prs(all_pos_unary_rules, all_neg_unary_rules, thresholds)
    core_prs = combined_model.core_model.get_prs(all_pos_core_rules, all_neg_core_rules, thresholds)
    is_prs = combined_model.is_model.get_prs(all_pos_is_rules, all_neg_is_rules, thresholds)
    cc_prs = combined_model.cc_model.get_prs(all_pos_cc_rules, all_neg_cc_rules, thresholds)
    core_tree_prs = combined_model.get_tree_prs(all_pos_bool_semantic_trees, all_neg_bool_semantic_trees, thresholds)

    return unary_prs, core_prs, is_prs, cc_prs, core_tree_prs


def evaluate_opt_model(combined_model, syntax_parses, annotations, match_parses, thresholds):
    tps, fps, tns, fns = defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int)

    for pk, local_syntax_parses in syntax_parses.iteritems():
        print ("="*80)
        match_parse = match_parses[pk]
        for number, syntax_parse in local_syntax_parses.iteritems():
            print (pk, number)
            opt_model = TextGreedyOptModel(combined_model)
            # opt_model = FullGreedyOptModel(combined_model, match_parse)

            pos_semantic_trees = set(annotation_to_semantic_tree(syntax_parse, annotation)
                                     for annotation in annotations[pk][number].values())

            pos_semantic_trees = set(t for t in pos_semantic_trees if t.content.signature.id != 'CC')

            tag_rules = combined_model.generate_tag_rules(syntax_parse)
            # tag_rules = set(itertools.chain(*[t.get_tag_rules() for t in pos_semantic_trees]))
            unary_rules = combined_model.generate_unary_rules(tag_rules)
            tag_rules = filter_tag_rules(combined_model.unary_model, tag_rules, unary_rules, 0.9)
            binary_rules = combined_model.generate_binary_rules(tag_rules)

            semantic_forest = SemanticForest(tag_rules, unary_rules, binary_rules)
            semantic_trees = semantic_forest.get_semantic_trees_by_type("truth").union(semantic_forest.get_semantic_trees_by_type('is'))
            semantic_trees = set(t for t in semantic_trees if combined_model.get_tree_score(t) > 0.01)
            neg_semantic_trees = semantic_trees - pos_semantic_trees

            for pst in pos_semantic_trees:
                print ("pos:", combined_model.get_tree_score(pst), pst)
            for nst in neg_semantic_trees:
                score = combined_model.get_tree_score(nst)
                if score > 0:
                    print ("neg:", score, nst)

            print ("")


            for th in thresholds:
                selected_trees = opt_model.optimize(semantic_trees, th)
                tp = len(selected_trees - neg_semantic_trees)
                fp = len(selected_trees - pos_semantic_trees)
                tn = len(neg_semantic_trees - selected_trees)
                fn = len(pos_semantic_trees - selected_trees)
                tps[th] += tp
                fps[th] += fp
                tns[th] += tn
                fns[th] += fn
            print ("-"*80)

    prs = {}

    for th in thresholds:
        p = float(tps[th])/max(1,tps[th]+fps[th])
        r = float(tps[th])/max(1,tps[th]+fns[th])
        prs[th] = p, r

    return prs


def test_rule_model():
    query = 'test'
    all_questions = geoserver_interface.download_questions(query)
    all_syntax_parses = questions_to_syntax_parses(all_questions)
    all_annotations = geoserver_interface.download_semantics(query)
    all_labels = geoserver_interface.download_labels(query)

    (tr_s, tr_a), (te_s, te_a) = split((all_syntax_parses, all_annotations), 0.5)

    tm = train_tag_model(all_syntax_parses, all_annotations)
    cm = train_semantic_model(tm, tr_s, tr_a)
    unary_prs, core_prs, is_prs, cc_prs, core_tree_prs = evaluate_rule_model(cm, te_s, te_a, np.linspace(0,1,101))

    plt.plot(core_tree_prs.keys(), core_tree_prs.values(), 'o')
    plt.show()
    plt.plot(unary_prs.keys(), unary_prs.values(), 'o')
    plt.show()
    plt.plot(core_prs.keys(), core_prs.values(), 'o')
    plt.show()
    plt.plot(is_prs.keys(), is_prs.values(), 'o')
    plt.show()
    plt.plot(cc_prs.keys(), cc_prs.values(), 'o')
    plt.show()

def test_opt_model():
    query = 'test'
    all_questions = geoserver_interface.download_questions(query)
    all_syntax_parses = questions_to_syntax_parses(all_questions)
    all_annotations = geoserver_interface.download_semantics(query)
    all_labels = geoserver_interface.download_labels(query)

    (tr_s, tr_a, tr_q), (te_s, te_a, te_q) = split([all_syntax_parses, all_annotations, all_questions], 0.5)
    tm = train_tag_model(all_syntax_parses, all_annotations)
    cm = train_semantic_model(tm, tr_s, tr_a)

    # te_m = questions_to_match_parses(te_q, all_labels)
    prs = evaluate_opt_model(cm, te_s, te_a, all_questions, np.linspace(-2,2,21))

    ps, rs = zip(*prs.values())
    plt.plot(prs.keys(), ps, 'o', label='precision')
    plt.plot(prs.keys(), rs, 'o', label='recall')
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=2, mode="expand", borderaxespad=0.)
    plt.show()


if __name__ == "__main__":
    # test_rule_model()
    test_opt_model()
