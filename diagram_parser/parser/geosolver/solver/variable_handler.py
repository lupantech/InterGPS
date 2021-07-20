import numpy as np

from geosolver.ontology.ontology_definitions import FormulaNode, VariableSignature, signatures, FunctionSignature, Node, \
    SetNode

__author__ = 'minjoon'

class VariableHandler(object):
    def __init__(self):
        self.variables = {}
        self.fixed = set()
        self.entities = []
        self.named_entities = {}
        self.free_variables = None

    def number(self, name, init=None):
        assert name not in self.variables
        if init is None:
            init = np.random.rand()
        self.variables[name] = init
        vn = FormulaNode(VariableSignature(name, 'number'), [])
        self.named_entities[name] = vn
        return vn

    def point(self, name, init=None):
        x_name = name + "_x"
        y_name = name + "_y"
        assert x_name not in self.variables
        assert y_name not in self.variables
        if init is None:
            init = np.random.rand(2)
        x, y = self.number(x_name, init[0]), self.number(y_name, init[1])
        vn = self.apply('Point', x, y)
        self.named_entities[name] = vn
        if len(self.fixed) == 0:
            self.fixed.add(x_name)
            self.fixed.add(y_name)
        """
        elif len(self.fixed) == 2:
            self.fixed.add(x_name)
        """
        return vn

    def line(self, p1, p2):
        return self.apply('Line', p1, p2)

    def circle(self, center, r=None, init=None):
        if init is None:
            init = np.random.rand()
        if r is None:
            r_name = "%s_r" % center.signature.id
            r = self.number(r_name, init=init)
        return self.apply('Circle', center, r)

    def add(self, formula_node, assignment=None):
        if assignment is None:
            assignment = {}
        if not isinstance(formula_node, Node):
            return formula_node

        if formula_node.is_leaf():
            assert isinstance(formula_node, FormulaNode)
            sig = formula_node.signature
            if isinstance(sig, FunctionSignature):
                return formula_node
            elif formula_node.signature.id in self.named_entities:
                return self.named_entities[sig.id]
            elif formula_node.return_type == "point":
                init = None
                if sig.id in assignment:
                    init = assignment[sig.id]
                return self.point(sig.id, init)
            elif formula_node.return_type == "number":
                init = None
                if sig.id in assignment:
                    init = assignment[sig.id]
                return self.number(sig.id, init)
            else:
                raise Exception()
        else:
            children = [self.add(child) for child in formula_node.children]
            if isinstance(formula_node, FormulaNode):
                formula = FormulaNode(formula_node.signature, children)
                if formula_node.signature.id in ['Line', 'Circle']:
                    self.entities.append(formula)
            else:
                formula = SetNode(children)
            return formula



    def apply(self, name, *args):
        vn = FormulaNode(signatures[name], args)
        if name in ['Point', 'Line', 'Circle']:
            self.entities.append(vn)
        return vn

    def get_free_variables(self):
        return {key: value for key, value in self.variables.iteritems() if key not in self.fixed}

    def vector_to_dict(self, vector, fix=True):
        """
        :param vector:
        :param padding:
        :return:
        """
        if fix:
            assert len(vector) + len(self.fixed) == len(self.variables)
        else:
            assert len(vector) == len(self.variables)
        if fix:
            if self.free_variables is None:
                self.free_variables = self.get_free_variables()
            variables = self.free_variables
        else:
            variables = self.variables
        out = dict(zip(variables.keys(), vector))
        if fix:
            for key in self.fixed: out[key] = self.variables[key]
        return out

    def dict_to_vector(self, fix=True):
        if fix:
            if self.free_variables is None:
                self.free_variables = self.get_free_variables()
            variables = self.free_variables
        else:
            variables = self.variables
        return variables.values()
