import itertools
import logging
import numpy as np
from geosolver.grounding.ground_formula import ground_formulas
from geosolver.grounding.states import MatchParse
from geosolver.text.complete_formulas import complete_formulas
from geosolver.text.rule import UnaryRule
from geosolver.text.rule_model import CombinedModel
from geosolver.text.semantic_tree import SemanticTreeNode

__author__ = 'minjoon'

class GreedyOptModel(object):

    def objective_function(self, semantic_trees):
        return 0.0

    def optimize(self, semantic_trees, threshold):
        return set()

class TextGreedyOptModel(GreedyOptModel):
    def __init__(self, combined_model):
        assert isinstance(combined_model, CombinedModel)
        self.combined_model = combined_model

    def optimize(self, semantic_trees, threshold, cc_trees=set()):
        selected = set()
        remaining = set(semantic_trees)

        curr_score = self.objective_function(selected)
        next_tree, next_score = self.get_next_tree(selected, remaining)
        if next_tree is None:
            print ("No legal next available.")
            return set()
        while next_score - curr_score > threshold:
            print ("%.2f, %r" % (next_score, next_tree))
            curr_score = next_score
            selected.add(next_tree)
            remaining.discard(next_tree)
            next_tree, next_score = self.get_next_tree(selected, remaining)
            if next_tree is None:
                print ("No legal next available.")
                break
            next_score = self.objective_function(selected.union([next_tree]))
            if len(selected) > 100:
                raise Exception()
        print ("")
        return selected

    def objective_function(self, semantic_trees, cc_trees=set()):
        if len(semantic_trees) == 0:
            return 0.0
        sum_log = sum(np.log(self.combined_model.get_tree_score(tree)) for tree in semantic_trees)
        return sum_log + self.get_coverage(semantic_trees, cc_trees)

    def get_coverage(self, semantic_trees, cc_trees):
        tag_rules = list(tr for semantic_tree in semantic_trees for tr in semantic_tree.get_tag_rules())
        if sum(tr.signature.id in ['What', 'Which', 'Find'] for tr in tag_rules) > 1:
            return -np.inf
        core_spans = set(tr.span for tr in tag_rules)
        for cc_tree in cc_trees:
            spans = set(tr.span for tr in cc_tree.get_tag_rules())
            if len(spans.intersection(core_spans)) > 0:
                core_spans = core_spans + spans
        cov = len(core_spans)
        return cov


    @staticmethod
    def pairwise_legal(a_tree, b_tree):
        """
        First, return 0 if one of them is self-referencing unary tree
        Do not penalize leaf redundancies
        Penalize everything else

        :param a_tree:
        :param b_tree:
        :return:
        """
        assert isinstance(a_tree, SemanticTreeNode)
        assert isinstance(b_tree, SemanticTreeNode)

        a_spans = set(node.content.span for node in a_tree)
        b_spans = set(node.content.span for node in b_tree)

        for a_span, b_span in itertools.product(a_spans, b_spans):
            a_set = set(range(*a_span))
            b_set = set(range(*b_span))
            if a_set != b_set and (a_set.issubset(b_set) or b_set.issubset(a_set)):
                return False

        common_spans = a_spans.intersection(b_spans)
        for span in common_spans:
            a_tags = a_tree.get_tag_rules_by_span(span)
            b_tags = b_tree.get_tag_rules_by_span(span)
            if a_tags != b_tags:
                return False
        return True


    def get_next_tree(self, selected, remaining):
        d = {each: self.objective_function(selected.union([each])) for each in remaining
             if all(TextGreedyOptModel.pairwise_legal(each, each_selected) for each_selected in selected)}
        if len(d) == 0:
            return None, None
        pair = max(d.items(), key=lambda pair: pair[1])
        return pair


class FullGreedyOptModel(TextGreedyOptModel):
    def __init__(self, combined_model, match_parse):
        super(FullGreedyOptModel, self).__init__(combined_model)
        assert isinstance(match_parse, MatchParse)
        self.match_parse = match_parse
        self.core_parse = match_parse.graph_parse.core_parse
        self.diagram_scores = {}

    def optimize(self, semantic_trees, threshold, cc_trees=set()):
        """
        for t in semantic_trees:
            print "%.3f %r %r" % (self.combined_model.get_tree_score(t), self.get_diagram_score(t), t)
        print ""
        """
        out = super(FullGreedyOptModel, self).optimize(semantic_trees, threshold, cc_trees)
        return out


    def get_diagram_score(self, formula, cc_formulas=set()):
        if formula in self.diagram_scores:
            return self.diagram_scores[formula]
        if formula.has_constant():
            self.diagram_scores[formula] = None
            return None

        completed_formulas = complete_formulas([formula], cc_formulas)

        try:
            grounded_formula = ground_formulas(self.match_parse, completed_formulas)[0]
            score = self.match_parse.graph_parse.core_parse.evaluate(grounded_formula).conf
        except Exception as e:
            # logging.exception(e)
            score = None
        self.diagram_scores[formula] = score
        return score

    def objective_function(self, semantic_trees, cc_trees=set()):
        if len(semantic_trees) == 0:
            return 0.0

        # sum_log = sum(np.log(self.combined_model.get_tree_score(tree)) for tree in semantic_trees)
        cov = self.get_coverage(semantic_trees, cc_trees)
        sum_log = sum(np.log(self.get_magic_score(t, cc_trees)) for t in semantic_trees)
        # sum_log = sum(np.log(magic(self.combined_model.get_tree_score(t), diagram_scores[t])) for t in semantic_trees)
        return cov + sum_log

    def get_magic_score(self, t, cc_trees):
        text_score = self.combined_model.get_tree_score(t)
        cc_formulas = set(t.to_formula() for t in cc_trees)
        diagram_score = self.get_diagram_score(t.to_formula(), cc_formulas=cc_formulas)
        if diagram_score is None:
            return text_score
        else:
            if diagram_score > text_score:
                return np.mean((text_score, diagram_score))
            else:
                return diagram_score

