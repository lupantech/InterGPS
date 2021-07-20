from geosolver.ontology.ontology_definitions import issubtype, Signature, VariableSignature
from geosolver.text.syntax_parser import SyntaxParse

__author__ = 'minjoon'

def _span_to_string(span):
    if span == "i":
        return span
    elif span[0] + 1 == span[1]:
        return "%d" % span[0]
    else:
        return "%d:%d" % (span[0], span[1]-1)

class SpanRule(object):
    pass

class BinarySpanRule(SpanRule):
    def __init__(self, parent_span, child_a_span, child_b_span):
        self.parent_span = parent_span
        self.child_a_span = child_a_span
        self.child_b_span = child_b_span

    def __eq__(self, other):
        return self.parent_span == other.parent_span and \
               self.child_a_span == other.child_a_span and self.child_b_span == other.child_b_span

    def __hash__(self):
        return hash((self.parent_span, self.child_a_span, self.child_b_span))

class TagRule(object):
    def __init__(self, syntax_parse, span, signature):
        assert isinstance(syntax_parse, SyntaxParse)
        assert isinstance(signature, Signature)
        self.syntax_parse = syntax_parse
        self.span = span
        self.signature = signature
        self.is_implicit = self.span == "i"
        self.string = "_".join(self.syntax_parse.words[i] for i in range(*self.span))

    def get_words(self):
        words = tuple(self.syntax_parse.words[idx] for idx in range(*self.span))
        return words

    def get_length(self):
        return self.span[1] - self.span[0]

    def is_single_word(self):
        return self.get_length() == 1

    def __hash__(self):
        return hash((self.span, self.signature))

    def __eq__(self, other):
        if not isinstance(other, TagRule):
            return False
        span = self.span == other.span
        sig = self.signature == other.signature
        return span and sig

    def __repr__(self):
        return "%s@%s[%s]" % (repr(self.signature), _span_to_string(self.span), self.string)

    def simple_repr(self):
        return self.signature.simple_repr()

    def serialized(self):
        out = {}
        out['class'] = self.__class__.__name__
        out['span'] = list(self.span)
        out['signature'] = self.signature.serialized()
        return out



class SemanticRule(object):
    pass

class UnaryRule(SemanticRule):
    def __init__(self, parent_tag_rule, child_tag_rule):
        #assert UnaryRule.val_func(parent_tag_rule, child_tag_rule)
        assert isinstance(parent_tag_rule, TagRule)
        assert isinstance(child_tag_rule, TagRule)
        self.syntax_parse = parent_tag_rule.syntax_parse
        self.parent_tag_rule = parent_tag_rule
        self.child_tag_rule = child_tag_rule

    def __repr__(self):
        return "%r->%r" % (self.parent_tag_rule, self.child_tag_rule)

    def __hash__(self):
        return hash((self.parent_tag_rule, self.child_tag_rule))

    def __eq__(self, other):
        return self.parent_tag_rule == other.parent_tag_rule and self.child_tag_rule == other.child_tag_rule

    @staticmethod
    def val_func(parent_tag_rule, child_tag_rule):
        valence = parent_tag_rule.signature.valence
        if valence == 0:
            return False
        elif valence == 1:
            return issubtype(child_tag_rule.signature.return_type, parent_tag_rule.signature.arg_types[0])
        elif valence == 2:
            c1 = issubtype(child_tag_rule.signature.return_type, parent_tag_rule.signature.arg_types[0])
            c2 = issubtype(parent_tag_rule.signature.arg_types[1], 'entity')
            return c1 and c2
        raise Exception()

    def is_self_ref(self):
        """
        self ref: ex. IsSquare@@1(quad@1)
        :return:
        """
        return self.parent_tag_rule.span == self.child_tag_rule.span and isinstance(self.child_tag_rule.signature, VariableSignature)





class BinaryRule(SemanticRule):
    def __init__(self, parent_tag_rule, child_a_tag_rule, child_b_tag_rule):
        if not BinaryRule.val_func(parent_tag_rule, child_a_tag_rule, child_b_tag_rule):
            raise Exception("%r %r %r" % (parent_tag_rule, child_a_tag_rule, child_b_tag_rule))
        assert isinstance(parent_tag_rule, TagRule)
        assert isinstance(child_a_tag_rule, TagRule)
        assert isinstance(child_b_tag_rule, TagRule)
        self.syntax_parse = parent_tag_rule.syntax_parse
        self.parent_tag_rule = parent_tag_rule
        self.child_a_tag_rule = child_a_tag_rule
        self.child_b_tag_rule = child_b_tag_rule

    @staticmethod
    def val_func(parent_tag_rule, a_tag_rule, b_tag_rule):
        valence = parent_tag_rule.signature.valence
        if valence == 2:
            a = issubtype(a_tag_rule.signature.return_type, parent_tag_rule.signature.arg_types[0])
            b = issubtype(b_tag_rule.signature.return_type, parent_tag_rule.signature.arg_types[1])
            return a and b
        else:
            return False

    def to_span_rule(self):
        return BinarySpanRule(self.parent_tag_rule.span, self.child_a_tag_rule.span, self.child_b_tag_rule.span)

    def __repr__(self):
        return "%r->%r|%r" % (self.parent_tag_rule, self.child_a_tag_rule, self.child_b_tag_rule)

    def __hash__(self):
        return hash((self.parent_tag_rule, self.child_a_tag_rule, self.child_b_tag_rule))

    def __eq__(self, other):
        return self.parent_tag_rule == other.parent_tag_rule and self.child_a_tag_rule == other.child_a_tag_rule and \
            self.child_b_tag_rule == other.child_b_tag_rule
