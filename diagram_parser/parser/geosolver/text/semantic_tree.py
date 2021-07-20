from collections import deque
from geosolver.ontology.ontology_definitions import FormulaNode
from geosolver.text.rule import UnaryRule, BinaryRule

__author__ = 'minjoon'


class SemanticTreeNode(FormulaNode):
    def __init__(self, content, children, parent=None, index=None):
        super(SemanticTreeNode, self).__init__(content.signature, children, parent, index)
        self.syntax_parse = content.syntax_parse
        self.content = content

    def __repr__(self):
        if len(self.children) == 0:
            return repr(self.content)
        else:
            args_string = ", ".join(repr(child) for child in self.children)
            return "%r(%s)" % (self.content, args_string)

    def serialized(self):
        out = super(SemanticTreeNode, self).serialized()
        out['content'] = self.content.serialized()
        return out

    def __hash__(self):
        return hash((self.content, tuple(self.children)))

    def __eq__(self, other):
        return self.content == other.content and tuple(self.children) == tuple(other.children)

    """
    def __iter__(self):
        queue = deque()
        queue.appendleft(self)
        while len(queue) > 0:
            current = queue.pop()
            for child in current.children:
                queue.appendleft(child)
            yield current
    """

    def is_unary(self):
        return len(self.children) == 1

    def is_binary(self):
        return len(self.children) == 2

    def to_formula(self):
        args = [child.to_formula() for child in self.children]
        return FormulaNode(self.content.signature, args)

    def get_tag_rules(self):
        tag_rules = set(node.content for node in self)
        return tag_rules

    def get_tag_rules_by_span(self, span):
        tag_rules = set(tag_rule for tag_rule in self.get_tag_rules() if tag_rule.span == span)
        return tag_rules

    def get_unary_rules(self):
        unary_rules = []
        for node in self:
            if node.is_unary():
                unary_rule = UnaryRule(node.content, node.children[0].content)
                unary_rules.append(unary_rule)
        return unary_rules

    def get_binary_rules(self):
        binary_rules = []
        for node in self:
            if node.is_binary():
                binary_rule = BinaryRule(node.content, node.children[0].content, node.children[1].content)
                binary_rules.append(binary_rule)
        return binary_rules

    def get_self_rule(self):
        if self.is_leaf():
            return None
        elif self.is_unary():
            unary_rule = UnaryRule(self.content, self.children[0].content)
            return unary_rule
        elif self.is_binary():
            binary_rule = BinaryRule(self.content, self.children[0].content, self.children[1].content)
            return binary_rule

        raise Exception()