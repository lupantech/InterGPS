from collections import defaultdict, Counter
import itertools
from operator import __mul__
from sklearn import svm
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from geosolver.grounding.ground_formula import _ground_variable
from geosolver.grounding.states import MatchParse
from geosolver.ontology.ontology_definitions import FunctionSignature, VariableSignature, issubtype, FormulaNode
from geosolver.ontology.ontology_definitions import signatures
from geosolver.text.feature_function import UnaryFeatureFunction, BinaryFeatureFunction
from geosolver.text.rule import TagRule, UnaryRule, BinaryRule
from geosolver.text.semantic_forest import SemanticForest
from geosolver.text.semantic_tree import SemanticTreeNode
from geosolver.utils.num import is_number
import numpy as np
from functools import reduce  

__author__ = 'minjoon'

def _normalize(counter):
    n = len(counter)
    new_counter = Counter({key: float(value) for key, value in counter.iteritems()})
    return new_counter

def filter_tag_rules(unary_model, tag_rules, unary_rules, th):
    filtered = set()
    tag_dict = {}
    for unary_rule in unary_rules:
        parent_tag = unary_rule.parent_tag_rule
        child_tag = unary_rule.child_tag_rule
        child_span = child_tag.span
        parent_span = parent_tag.span
        if isinstance(child_tag.signature, VariableSignature) and unary_model.get_score(unary_rule) > th:
            tag_dict[child_span] = child_tag
            tag_dict[parent_span] = parent_tag

    for tag_rule in tag_rules:
        if tag_rule.span in tag_dict:
            if tag_rule == tag_dict[tag_rule.span]:
                filtered.add(tag_rule)
        else:
            filtered.add(tag_rule)

    return filtered

def filter_unary_rules(tag_rules, unary_rules):
    filtered = set()
    for unary_rule in unary_rules:
        parent_tag, child_tag = unary_rule.parent_tag_rule, unary_rule.child_tag_rule
        if parent_tag in tag_rules and child_tag in tag_rules:
            filtered.add(unary_rule)
    return filtered


class Model(object):
    def get_score(self, rule):
        return 0.0

    def get_prs(self, pos_rules, neg_rules, ths):
        tps, fps, tns, fns = defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int)


        for pr in pos_rules:
            score = self.get_score(pr)
            for th in ths:
                if score >= th: tps[th] += 1
                else: fns[th] += 1

        for nr in neg_rules:
            score = self.get_score(nr)
            for th in ths:
                if score >= th: fps[th] += 1
                else: tns[th] += 1

        prs = {}
        for th in ths:
            p = float(tps[th])/(max(1,tps[th])+fps[th])
            r = float(tps[th])/(max(1,tps[th])+fns[th])
            prs[th] = p, r
        return prs


class TagModel(object):
    pass


class NaiveTagModel(TagModel):
    """
    It predicts 0 for unseen tag rule, and 1 for seen.
    """
    def __init__(self):
        self.tag_rules = []
        self.lexicon = defaultdict(set)

    def update(self, tag_rules):
        self.tag_rules.extend(tag_rules)
        for tag_rule in tag_rules:
            entry = (tag_rule.signature.return_type, tag_rule.signature.name)
            self.lexicon[tag_rule.get_words()].add(entry)

    def fit(self):
        pass

    def get_score(self, tag_rule):
        words = tag_rule.get_words()
        if words in self.lexicon and tag_rule.signature.name in self.lexicon[words]:
            return 1.0
        return 0.0

    def generate_tag_rules(self, syntax_parse):
        tag_rules = set()
        for span in syntax_parse.iterate_spans():
            prev_word = syntax_parse.get_word(span[0]-1)
            if prev_word is not None:
                prev_word = prev_word.lower()
            words = syntax_parse.get_words(span)
            if len(words) == 1:
                return_types = []
                word = words[0]
                if is_number(word):
                    tag_rule = TagRule(syntax_parse, span, FunctionSignature(word, 'number', []))
                    tag_rules.add(tag_rule)
                    continue
                elif word.startswith("@v"):
                    return_types.append('number')

                elif word.islower() and len(word) == 1:
                    pos = syntax_parse.get_pos_by_index(span[0])
                    if pos == "DT":
                        continue
                    return_types.append('line')
                    return_types.append('angle')
                    return_types.append('number')

                elif word.isupper():
                    if len(word) == 1:
                        pos = syntax_parse.get_pos_by_index(span[0])
                        if pos == "DT":
                            continue


                        if prev_word in ('circle', 'circles'):
                            return_types.append('circle')
                        elif prev_word in ('angle', 'angles'):
                            return_types.append('angle')
                        elif prev_word in ('line', 'lines'):
                            return_types.append('line')
                        else:
                            return_types.append('point')
                    elif len(word) == 2:
                        if prev_word in ('arc', 'arcs'):
                            return_types.append('arc')
                        else:
                            return_types.extend(['number', 'line'])
                    elif len(word) == 3: return_types.extend(['angle', 'triangle', 'number'])
                    elif len(word) == 4: return_types.extend(['quad'])
                    elif len(word) == 6: return_types.extend(['hexagon'])
                    else: return_types.extend(['polygon'])
                curr_tag_rules = [TagRule(syntax_parse, span, VariableSignature((span,rt), rt, name=word))
                                      for rt in return_types]
                for tag_rule in curr_tag_rules: tag_rules.add(tag_rule)
                if len(curr_tag_rules) > 0:
                    continue

            if words in self.lexicon:
                for return_type, name in self.lexicon[words]:
                    if name[0].isupper():
                        signature = signatures[name]
                    else:
                        signature = VariableSignature((span,return_type), return_type, name=name)
                    tag_rule = TagRule(syntax_parse, span, signature)
                    tag_rules.add(tag_rule)
        return tag_rules

    def print_lexicon(self):
        for words, entries in self.lexicon.iteritems():
            print ("%s: %s" % (" ".join(words), ", ".join(" ".join(entry) for entry in entries)))


class SemanticModel(Model):
    pass

class UnaryModel(SemanticModel):
    @staticmethod
    def val_func(parent_tag_rule, child_tag_rule):
        return False

    def generate_unary_rules(self, tag_rules):
        unary_rules = set()
        for parent_tag_rule, child_tag_rule in itertools.permutations(tag_rules, 2):
            if self.__class__.val_func(parent_tag_rule, child_tag_rule):
                unary_rule = UnaryRule(parent_tag_rule, child_tag_rule)
                unary_rules.add(unary_rule)
        return unary_rules


class BinaryModel(SemanticModel):
    @staticmethod
    def val_func(parent_tag_rule, a_tag_rule, b_tag_rule):
        raise Exception()

    def generate_binary_rules(self, tag_rules):
        binary_rules = set()
        for parent_tag_rule, a_tag_rule, b_tag_rule in itertools.permutations(tag_rules, 3):
            if self.__class__.val_func(parent_tag_rule, a_tag_rule, b_tag_rule):
                binary_rule = BinaryRule(parent_tag_rule, a_tag_rule, b_tag_rule)
                binary_rules.add(binary_rule)
        return binary_rules


class CombinedModel(Model):
    def __init__(self, tag_model, unary_model, core_model, is_model, cc_model):
        assert isinstance(tag_model, TagModel)
        assert isinstance(unary_model, UnaryModel)
        assert isinstance(core_model, BinaryModel)
        assert isinstance(is_model, BinaryModel)
        assert isinstance(cc_model, BinaryModel)
        self.tag_model = tag_model
        self.unary_model = unary_model
        self.core_model = core_model
        self.is_model = is_model
        self.cc_model = cc_model

    def get_score(self, rule):
        if isinstance(rule, UnaryRule):
            return self.unary_model.get_score(rule)
        elif isinstance(rule, BinaryRule):
            if rule.parent_tag_rule.signature.id == "CC":
                return self.cc_model.get_score(rule)
            elif rule.parent_tag_rule.signature.id == "Is":
                return self.is_model.get_score(rule)
            else:
                return self.core_model.get_score(rule)
        raise Exception()

    def get_tree_score(self, semantic_tree):
        assert isinstance(semantic_tree, SemanticTreeNode)
        unary_rules = semantic_tree.get_unary_rules()
        binary_rules = semantic_tree.get_binary_rules()
        scores = [self.get_score(rule) for rule in itertools.chain(unary_rules, binary_rules)]
        return reduce(__mul__, scores, 1)

    def generate_unary_rules(self, tag_rules):
        return self.unary_model.generate_unary_rules(tag_rules)

    def generate_binary_rules(self, tag_rules):
        core_rules = self.core_model.generate_binary_rules(tag_rules)
        is_rules = self.is_model.generate_binary_rules(tag_rules)
        cc_rules = self.cc_model.generate_binary_rules(tag_rules)
        out = set(itertools.chain(core_rules, is_rules, cc_rules))
        return out

    def generate_tag_rules(self, syntax_parse):
        return self.tag_model.generate_tag_rules(syntax_parse)

    def get_tree_prs(self, pos_trees, neg_trees, ths):
        tps, fps, tns, fns = defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int)

        for pt in pos_trees:
            score = self.get_tree_score(pt)
            for th in ths:
                if score >= th: tps[th] += 1
                else: fns[th] += 1

        for nt in neg_trees:
            score = self.get_tree_score(nt)
            for th in ths:
                if score >= th: fps[th] += 1
                else: tns[th] += 1

        prs = {}
        for th in ths:
            p = float(tps[th])/(tps[th]+fps[th])
            r = float(tps[th])/(tps[th]+fns[th])
            prs[th] = p, r
        return prs

    def get_semantic_forest(self, syntax_parse):
        tag_rules = self.generate_tag_rules(syntax_parse)
        unary_rules = self.generate_unary_rules(tag_rules)
        tag_rules = filter_tag_rules(self.unary_model, tag_rules, unary_rules, 0.9)
        unary_rules = filter_unary_rules(tag_rules, unary_rules)
        binary_rules = self.generate_binary_rules(tag_rules)
        semantic_forest = SemanticForest(tag_rules, unary_rules, binary_rules)
        return semantic_forest


class NaiveUnaryModel(UnaryModel):
    def __init__(self, max_word_distance):
        self.max_word_distance = max_word_distance

    @staticmethod
    def val_func(p, c):
        if p.signature.id in ('Is', 'CC'):
            return False
        return UnaryRule.val_func(p, c)

    def get_score(self, unary_rule):
        assert isinstance(unary_rule, UnaryRule)
        syntax_parse = unary_rule.syntax_parse
        distance = syntax_parse.distance_between_spans(unary_rule.child_tag_rule.span, unary_rule.parent_tag_rule.span)
        if distance == 0:
            return 1.0
        if distance > self.max_word_distance:
            return 0.0
        return 1.0/distance


class NaiveBinaryModel(BinaryModel):
    def __init__(self, max_word_distance):
        self.max_word_distance = max_word_distance

    def get_score(self, binary_rule):
        assert isinstance(binary_rule, BinaryRule)
        syntax_parse = binary_rule.syntax_parse
        da = syntax_parse.distance_between_spans(binary_rule.child_a_tag_rule.span, binary_rule.parent_tag_rule.span)
        db = syntax_parse.distance_between_spans(binary_rule.child_b_tag_rule.span, binary_rule.parent_tag_rule.span)
        if da == 0: sa = 1
        elif da > self.max_word_distance: sa = 0
        else: sa = 1.0/da
        if db == 0: sb = 1
        elif db > self.max_word_distance: sb = 0
        else: sb = 1.0/db
        return np.mean([sa, sb])


class NaiveCoreModel(NaiveBinaryModel):
    @staticmethod
    def val_func(p, a, b):
        if p.signature.id in ('Is', 'CC') or a.signature.id in ('Is', 'CC') or b.signature.id in ('Is', 'CC'):
            return False
        return BinaryRule.val_func(p, a, b)


class NaiveIsModel(NaiveBinaryModel):
    @staticmethod
    def val_func(p, a, b):
        if p.signature.id != "Is":
            return False
        if not issubtype(a.signature.return_type, b.signature.return_type) and \
                not issubtype(b.signature.return_type, a.signature.return_type):
            return False
        if not (issubtype(a.signature.return_type, 'number') or issubtype(a.signature.return_type, 'entity')):
            return False
        return BinaryRule.val_func(p, a, b)

    def get_score(self, binary_rule):
        assert isinstance(binary_rule, BinaryRule)
        b_to_a = binary_rule.syntax_parse.relation_between_spans(binary_rule.child_b_tag_rule.span,
                                                                 binary_rule.child_a_tag_rule.span, True)
        b_to_p = binary_rule.syntax_parse.relation_between_spans(binary_rule.child_b_tag_rule.span,
                                                                 binary_rule.parent_tag_rule.span, True)
        p_to_a = binary_rule.syntax_parse.relation_between_spans(binary_rule.parent_tag_rule.span,
                                                                 binary_rule.child_a_tag_rule.span, True)
        p_to_b = binary_rule.syntax_parse.relation_between_spans(binary_rule.parent_tag_rule.span,
                                                                 binary_rule.child_b_tag_rule.span, True)
        if b_to_p == "cop" and b_to_a == "nsubj":
            return 1.0
        elif p_to_a == "nsubj" and p_to_b == "dobj":
            return 1.0
        return 0.0


class NaiveCCModel(NaiveBinaryModel):
    @staticmethod
    def val_func(p, a, b):
        if p.signature.id != "CC":
            return False
        if a.signature.valence > 0:
            return False
        if b.signature.valence > 0:
            return False
        if a.signature.return_type != b.signature.return_type:
            return False
        return BinaryRule.val_func(p, a, b)

    def get_score(self, binary_rule):
        assert isinstance(binary_rule, BinaryRule)
        a_to_b = binary_rule.syntax_parse.relation_between_spans(binary_rule.child_a_tag_rule.span,
                                                                 binary_rule.child_b_tag_rule.span, True)
        a_to_p = binary_rule.syntax_parse.relation_between_spans(binary_rule.child_a_tag_rule.span,
                                                                 binary_rule.parent_tag_rule.span, True)
        if a_to_p == "cc" and (a_to_b == "conj" or a_to_b == "advmod"):
            return 1.0
        return 0.0


class RFUnaryModel(UnaryModel):
    def __init__(self):
        self.positive_unary_rules = []
        self.negative_unary_rules = []
        self.feature_function = None
        self.classifier = None
        self.scores = {}

    @staticmethod
    def val_func(p, c):
        if p.signature.id in ('Is', 'CC'):
            return False
        return UnaryRule.val_func(p, c)

    def update(self, tag_rules, positive_unary_rules):
        all_unary_rules = self.generate_unary_rules(tag_rules)
        negative_unary_rules = all_unary_rules - positive_unary_rules
        self.positive_unary_rules.extend(positive_unary_rules)
        self.negative_unary_rules.extend(negative_unary_rules)

    def fit(self):
        print ("Fitting %s:" % self.__class__.__name__)
        print ("# of positive examples:", len(self.positive_unary_rules))
        print ("# of negative examples:", len(self.negative_unary_rules))
        self.feature_function = UnaryFeatureFunction(self.positive_unary_rules + self.negative_unary_rules)
        X = []
        y = []
        for pur in self.positive_unary_rules:
            X.append(self.feature_function.map(pur))
            y.append(1)
        for nur in self.negative_unary_rules:
            X.append(self.feature_function.map(nur))
            y.append(0)

        print ("length of feature vector:", np.shape(X)[1])

        cw = {0: len(self.positive_unary_rules), 1: len(self.negative_unary_rules)}
        # self.classifier = RandomForestClassifier(class_weight='auto', n_estimators=30) # RandomForestClassifier()
        # self.classifier = SVC(probability=True, class_weight='auto')
        self.classifier = LogisticRegression(class_weight='auto')
        self.classifier.fit(X, y)

    def get_score(self, ur):
        if ur in self.scores:
            return self.scores[ur]
        x = self.feature_function.map(ur)
        probas = self.classifier.predict_proba([x])
        score = probas[0][1]
        self.scores[ur] = score
        return score


class RFCoreModel(BinaryModel):
    def __init__(self):
        self.positive_binary_rules = []
        self.negative_binary_rules = []
        self.feature_function = None
        self.classifier = None
        self.feature_function_class = BinaryFeatureFunction
        self.classifier_class = RandomForestClassifier
        self.scores = {}

    @staticmethod
    def val_func(p, a, b):
        if p.signature.id in ('Is', 'CC') or a.signature.id in ('Is', 'CC') or b.signature.id in ('Is', 'CC'):
            return False
        return BinaryRule.val_func(p, a, b)

    def update(self, tag_rules, positive_binary_rules):
        all_binary_rules = self.generate_binary_rules(tag_rules)
        negative_binary_rules = all_binary_rules - positive_binary_rules
        self.positive_binary_rules.extend(positive_binary_rules)
        self.negative_binary_rules.extend(negative_binary_rules)

    def fit(self):
        print ("Fitting %s:" % self.__class__.__name__)
        print ("# of positive examples:", len(self.positive_binary_rules))
        print ("# of negative examples:", len(self.negative_binary_rules))
        self.feature_function = self.feature_function_class(self.positive_binary_rules + self.negative_binary_rules)
        X = []
        y = []
        for pbr in self.positive_binary_rules:
            X.append(self.feature_function.map(pbr))
            y.append(1)
        for nbr in self.negative_binary_rules:
            X.append(self.feature_function.map(nbr))
            y.append(0)

        print ("length of feature vector:", np.shape(X)[1])

        cw = {0: len(self.positive_binary_rules), 1: len(self.negative_binary_rules)}
        # self.classifier = self.classifier_class(class_weight='auto', n_estimators=30)
        # self.classifier = SVC(probability=True, class_weight='auto')
        self.classifier = LogisticRegression(class_weight='auto')
        self.classifier.fit(X, y)

    def get_score(self, br):
        if br in self.scores:
            return self.scores[br]
        x = self.feature_function.map(br)
        probas = self.classifier.predict_proba([x])
        score = probas[0][1]
        self.scores[br] = score
        return score


class RFIsModel(RFCoreModel):
    @staticmethod
    def val_func(p, a, b):
        if p.signature.id != "Is":
            return False
        if not issubtype(a.signature.return_type, b.signature.return_type) and \
                not issubtype(b.signature.return_type, a.signature.return_type):
            return False
        if not (issubtype(a.signature.return_type, 'number') or issubtype(a.signature.return_type, 'entity')):
            return False
        return BinaryRule.val_func(p, a, b)

    def fit(self):
        print ("Fitting %s:" % self.__class__.__name__)
        print ("# of positive examples:", len(self.positive_binary_rules))
        print ("# of negative examples:", len(self.negative_binary_rules))
        self.feature_function = self.feature_function_class(self.positive_binary_rules + self.negative_binary_rules)
        X = []
        y = []
        for pbr in self.positive_binary_rules:
            X.append(self.feature_function.map(pbr))
            y.append(1)
        for nbr in self.negative_binary_rules:
            X.append(self.feature_function.map(nbr))
            y.append(0)

        print ("length of feature vector:", np.shape(X)[1])

        cw = {0: len(self.positive_binary_rules), 1: len(self.negative_binary_rules)}
        # self.classifier = self.classifier_class(class_weight='auto', n_estimators=30)
        # self.classifier = SVC(probability=True, class_weight='auto')
        self.classifier = LogisticRegression(class_weight='auto')
        self.classifier.fit(X, y)


class RFCCModel(RFCoreModel):
    @staticmethod
    def val_func(p, a, b):
        if p.signature.id != "CC":
            return False
        if a.signature.valence > 0:
            return False
        if b.signature.valence > 0:
            return False
        if a.signature.return_type != b.signature.return_type:
            return False
        return BinaryRule.val_func(p, a, b)

    def update(self, tag_rules, positive_binary_rules):
        all_binary_rules = self.generate_binary_rules(tag_rules)
        positive_span_rules = set(r.to_span_rule() for r in positive_binary_rules)
        for binary_rule in all_binary_rules:
            if binary_rule.to_span_rule() in positive_span_rules:
                self.positive_binary_rules.append(binary_rule)
            else:
                self.negative_binary_rules.append(binary_rule)

    def fit(self):
        print ("Fitting %s:" % self.__class__.__name__)
        print ("# of positive examples:", len(self.positive_binary_rules))
        print ("# of negative examples:", len(self.negative_binary_rules))
        self.feature_function = self.feature_function_class(self.positive_binary_rules + self.negative_binary_rules)
        X = []
        y = []
        for pbr in self.positive_binary_rules:
            X.append(self.feature_function.map(pbr))
            y.append(1)
        for nbr in self.negative_binary_rules:
            X.append(self.feature_function.map(nbr))
            y.append(0)

        print ("length of feature vector:", np.shape(X)[1])

        cw = {0: len(self.positive_binary_rules), 1: len(self.negative_binary_rules)}
        self.classifier = self.classifier_class(class_weight='auto')
        # self.classifier = SVC(probability=True, class_weight='auto')
        # self.classifier = LogisticRegression(class_weight='auto')
        self.classifier.fit(X, y)
