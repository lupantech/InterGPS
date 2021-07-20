from collections import defaultdict
from geosolver.ontology.ontology_definitions import issubtype
from geosolver.text.rule import UnaryRule, BinaryRule, TagRule

__author__ = 'minjoon'

class FeatureFunction(object):
    def map(self, rule):
        pass

class TagFeatureFunction(FeatureFunction):
    def __init__(self, tag_rules):
        self.return_type_set = {'line', 'circle', 'arc', 'polygon', 'number', 'angle', 'truth'}
        self.pos_set = set()
        self.key_rels = ('compound',)
        self.key_nbrs = defaultdict(set)
        for tag_rule in tag_rules:
            assert isinstance(tag_rule, TagRule)
            sp = tag_rule.syntax_parse
            nbrs = sp.get_neighbors(tag_rule.span)
            for to, rel in nbrs.items():
                if rel in self.key_rels:
                    self.key_nbrs[rel].add(sp.get_word(to))

            # self.return_type_set.add(tag_rule.signature.return_type)
            self.pos_set.add(sp.get_pos_by_span(tag_rule.span))

    def map(self, tr):
        assert isinstance(tr, TagRule)
        sp = tr.syntax_parse
        out = []

        for ref_rt in self.return_type_set:
            out.append(int(issubtype(tr.signature.return_type, ref_rt)))
        for ref_pos in self.pos_set:
            out.append(int(ref_pos == sp.get_pos_by_span(tr.span)))

        nbrs = sp.get_neighbors(tr.span)
        pairs = set((rel, sp.get_word(key)) for key, rel in nbrs.items())
        for key_rel in self.key_rels:
            for nbr in self.key_nbrs:
                pair = (key_rel, nbr)
                out.append(int(pair in pairs))

        return tuple(out)


class UnaryFeatureFunction(FeatureFunction):
    def __init__(self, unary_rules):
        self.p_ff = TagFeatureFunction(ur.parent_tag_rule for ur in unary_rules)
        self.c_ff = TagFeatureFunction(ur.child_tag_rule for ur in unary_rules)

        self.nbr_rel_set = set()
        self.mid_pos_set = set()
        self.graph_dist_set = {0, 1, 2, 3, 4}
        self.plain_dist_set = set() #{1, 2, 3, 4}
        self.p_pos_set = set()
        self.c_pos_set = set()
        self.p_return_type_set = set()
        self.c_return_type_set = set()

        for unary_rule in unary_rules:
            assert isinstance(unary_rule, UnaryRule)
            sp, p, c = unary_rule.syntax_parse, unary_rule.parent_tag_rule, unary_rule.child_tag_rule
            graph_distance = sp.distance_between_spans(p.span, c.span)
            if graph_distance == 1:
                rel = sp.relation_between_spans(p.span, c.span)
                self.nbr_rel_set.add(rel)
            elif graph_distance == 2:
                path = sp.shortest_path_between_spans(p.span, c.span)
                assert len(path) == 3
                mid_pos = sp.get_pos_by_index(path[1])
                self.mid_pos_set.add(mid_pos)

            """
            self.p_pos_set.add(sp.get_pos_by_span(p.span))
            self.c_pos_set.add(sp.get_pos_by_span(c.span))
            self.p_return_type_set.add(p.signature.return_type)
            self.c_return_type_set.add(c.signature.return_type)
            """


    def map(self, ur):
        assert isinstance(ur, UnaryRule)
        out = []
        sp, p, c = ur.syntax_parse, ur.parent_tag_rule, ur.child_tag_rule
        d = sp.distance_between_spans(p.span, c.span)
        pd = sp.plain_distance_between_spans(p.span, c.span, True)

        for ref_d in self.graph_dist_set:
            out.append(int(d == ref_d))
        for ref_pd in self.plain_dist_set:
            out.append(int(abs(pd) == ref_pd))
        for ref_rel in self.nbr_rel_set:
            out.append(int(d == 1 and ref_rel == sp.relation_between_spans(p.span, c.span)))
        for ref_tag in self.mid_pos_set:
            out.append(int(d == 2 and ref_tag == sp.get_pos_by_index(sp.shortest_path_between_spans(p.span, c.span)[1])))
        # out.append(pd)

        """
        for ref_p_tag in self.p_pos_set:
            out.append(int(ref_p_tag == sp.get_pos_by_span(p.span)))
        for ref_c_tag in self.c_pos_set:
            out.append(int(ref_c_tag == sp.get_pos_by_span(c.span)))

        for ref_p_return_type in self.p_return_type_set:
            out.append(int(ref_p_return_type == p.signature.return_type))
        for ref_c_return_type in self.p_return_type_set:
            out.append(int(ref_c_return_type == p.signature.return_type))
        """

        out = tuple(out)
        return out + self.p_ff.map(p) + self.c_ff.map(c)


def binary_rule_to_unary_rules(binary_rule):
    assert isinstance(binary_rule, BinaryRule)
    p, a, b = binary_rule.parent_tag_rule, binary_rule.child_a_tag_rule, binary_rule.child_b_tag_rule
    pa = UnaryRule(p, a)
    pb = UnaryRule(p, b)
    ab = UnaryRule(a, b)
    return pa, pb, ab


class BinaryFeatureFunction(FeatureFunction):
    def __init__(self, binary_rules):
        pas, pbs, abs = zip(*[binary_rule_to_unary_rules(br) for br in binary_rules])
        self.pa_ff = UnaryFeatureFunction(pas)
        self.pb_ff = UnaryFeatureFunction(pbs)
        self.ab_ff = UnaryFeatureFunction(abs)

    def map(self, rule):
        pa, pb, ab = binary_rule_to_unary_rules(rule)
        pa_fv = self.pa_ff.map(pa)
        pb_fv = self.pa_ff.map(pb)
        ab_fv = self.pa_ff.map(ab)
        fv = pa_fv + pb_fv + ab_fv
        return fv
