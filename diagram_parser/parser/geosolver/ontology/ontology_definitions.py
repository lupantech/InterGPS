import itertools
import networkx as nx
from geosolver.utils.num import is_number

__author__ = 'minjoon'


class Signature(object):
    def __init__(self, id_, return_type, valence=0, name=None):
        self.id = id_
        self.return_type = return_type
        if name is None:
            if isinstance(id_, str):
                name = id_
            else:
                name = repr(id_)
        self.name = name
        self.valence = valence

    def __eq__(self, other):
        assert isinstance(other, Signature)
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def simple_repr(self):
        return self.name

    def serialized(self):
        return {"id": self.id, "return_type": self.return_type, "valence": self.valence, "name": self.name,
                "class": self.__class__.__name__}

class FunctionSignature(Signature):
    def __init__(self, id_, return_type, arg_types, arg_pluralities=None, is_symmetric=False, name=None):
        super(FunctionSignature, self).__init__(id_, return_type, len(arg_types), name=name)
        self.arg_types = arg_types
        if arg_pluralities is None:
            arg_pluralities = (False,) * len(arg_types)
        self.arg_pluralities = arg_pluralities
        self.is_symmetric = is_symmetric
        self.valence = len(arg_types)

    def __repr__(self):
        return self.name

    def simple_repr(self):
        return self.name

    def serialized(self):
        out = super(FunctionSignature, self).serialized()
        out['arg_types'] = list(self.arg_types)
        return out


class VariableSignature(Signature):
    def __init__(self, id_, return_type, name=None):
        super(VariableSignature, self).__init__(id_, return_type, 0, name=name)

    def __repr__(self):
        return "$%s:%s" % (self.name, self.return_type)

    def simple_repr(self):
        return self.name

    def is_ref(self):
        """
        starts with '@'
        :return:
        """
        if isinstance(self.name, str):
            return self.name.startswith("@")
        return False


class Node(object):
    def __init__(self, children, parent=None, index=None):
        self.parent = parent
        self.index = index
        self.children = children
        self.valence = len(children)
        for idx, child in enumerate(children):
            if isinstance(child, Node):
                child.parent = self
                child.index = idx

    def serialized(self):
        serialized_children = [child.serialized() for child in self.children]
        out = {'children': serialized_children, 'class': self.__class__.__name__}
        return out

    def is_leaf(self):
        return len(self.children) == 0

    def replace_node(self, tester, getter=None):
        args = [child.replace_node(tester, getter) for child in self.children]
        out = self.__class__(args, self.parent, self.index)
        test = tester(out)
        if bool(test):
            if getter is None:
                return test
            return getter(out)
        return out

    def __iter__(self):
        yield self
        for x in itertools.chain(*[iter(child) for child in self.children]):
            yield x

    def __len__(self):
        l = 1
        for child in self.children:
            l += child.__len__()
        return l

    def is_singular(self):
        return len(self.children) == 1

    def is_plural(self):
        return len(self.children) > 1

    def has_signature(self, id_):
        return any(not is_number(child) and child.has_signature(id_) for child in self.children)

    def has_constant(self):
        return any(not isinstance(child, Node) or child.has_constant() for child in self.children)

    def is_grounded(self, ids=()):
        return all(not isinstance(child, Node) or child.is_grounded(ids) for child in self.children)

    def get_nodes(self, tester):
        return [node for node in self if tester(node)]

    def get_grounded_subformula(self, ids=()):
        """
        Since at most bianry, there exists at most single biggest grouded subformula.
        Returns None if it doesn't exist

        :param ids:
        :return:
        """
        if self.is_grounded(ids):
            return self
        for child in self.children:
            return child.get_grounded_subformula(ids)
        return None

    def zip(self, other):
        if self.is_leaf() or not isinstance(other, Node) or other.is_leaf() or len(self.children) != len(other.children):
            return ZippedNode([self, other], [])
        children = [sc.zip(oc) for sc, oc in zip(self.children, other.children)]
        return ZippedNode([self, other], children)


class FormulaNode(Node):
    def __init__(self, signature, children, parent=None, index=None):
        self.signature = signature
        super(FormulaNode, self).__init__(children, parent, index)
        self.return_type = signature.return_type

    def replace_signature(self, tester, getter):
        """
        iterate through all formula nodes and if tester(signature) is true,
         then replace_signature it with getter(signature).
        :param function tester:
        :param function getter:
        :return:
        """
        new_sig = self.signature
        args = [child.replace_signature(tester, getter) for child in self.children]
        if tester(self.signature):
            new_sig = getter(self.signature)
        return FormulaNode(new_sig, args)

    def replace_node(self, tester, getter=None):
        args = []
        for child in self.children:
            if isinstance(child, Node):
                args.append(child.replace_node(tester, getter))
            else:
                args.append(child)
        out = self.__class__(self.signature, args, self.parent, self.index)
        test = tester(out)
        if bool(test):
            if getter is None:
                return test
            return getter(out)
        return out

    def __hash__(self):
        if isinstance(self.signature, FunctionSignature) and self.signature.is_symmetric:
            return hash((self.signature, frozenset(self.children)))
        return hash((self.signature, tuple(self.children)))

    def __eq__(self, other):
        if isinstance(self.signature, FunctionSignature) and self.signature.is_symmetric:
            return self.signature == other.signature and frozenset(self.children) == frozenset(other.children)
        return self.signature == other.signature and tuple(self.children) == tuple(other.children)

    def __add__(self, other):
        current = signatures['Add']
        return FormulaNode(current, [self, other])

    def __radd__(self, other):
        current = signatures['Add']
        return FormulaNode(current, [other, self])

    def __mul__(self, other):
        current = signatures['Mul']
        return FormulaNode(current, [self, other])

    def __rmul__(self, other):
        current = signatures['Mul']
        return FormulaNode(current, [other, self])

    def __sub__(self, other):
        current = signatures['Sub']
        return FormulaNode(current, [self, other])

    def __rsub__(self, other):
        current = signatures['Sub']
        return FormulaNode(current, [other, self])

    def __div__(self, other):
        current = signatures['Div']
        return FormulaNode(current, [self, other])

    def __rdiv__(self, other):
        current = signatures['Div']
        return FormulaNode(current, [other, self])

    def __pow__(self, power, modulo=None):
        current = signatures['Pow']
        return FormulaNode(current, [self, power])

    def __rpow__(self, power, modulo=None):
        current = signatures['Pow']
        return FormulaNode(current, [power, self])

    def __ge__(self, other):
        current = signatures['Ge']
        return FormulaNode(current, [self, other])

    def __lt__(self, other):
        current = signatures['Lt']
        return FormulaNode(current, [self, other])

    def __repr__(self):
        if isinstance(self.signature, VariableSignature):
            return repr(self.signature)
        return "%r(%s)" % (self.signature, ",".join(repr(child) for child in self.children))

    def simple_repr(self):
        if len(self.children) == 0:
            return self.signature.simple_repr()
        else:
            args_string = ", ".join(child.simple_repr() for child in self.children)
            return "%s(%s)" % (self.signature.simple_repr(), args_string)

    def serialized(self):
        out = super(FormulaNode, self).serialized()
        out['signature'] = self.signature.serialized()
        return out

    def has_signature(self, id_):
        if self.signature.id == id_:
            return True
        return any(not is_number(child) and child.has_signature(id_) for child in self.children)

    def has_constant(self):
        if self.is_leaf():
            if isinstance(self.signature, VariableSignature):
                return False
            return True
        return any(not isinstance(child, Node) or child.has_constant() for child in self.children)

    def is_grounded(self, ids=[]):
        """
        Determines if the formula's variables are only made of ids
        :param core_parse:
        :return:
        """
        if self.is_leaf():
            if isinstance(self.signature, VariableSignature):
                return self.signature.id in ids
            return True
        return all(not isinstance(child, Node) or child.is_grounded(ids) for child in self.children)


class ZippedNode(Node):
    def __init__(self, nodes, children):
        super(ZippedNode, self).__init__(children)
        self.nodes = nodes

    def __repr__(self):
        if len(self.children) == 0:
            return "[%s]" % (",".join(repr(node) for node in self.nodes))
        return "[%s](%s)" % (",".join(repr(node) for node in self.nodes), ",".join(repr(child) for child in self.children))


class SetNode(Node):
    def __init__(self, children, parent=None, index=None, head_index=0):
        super(SetNode, self).__init__(children, parent, index)
        self.head = children[head_index]

    def __repr__(self):
        return "{%s}" % ",".join(repr(child) for child in self.children)

    def simple_repr(self):
        return "{%s}" % ",".join(child.simple_repr() for child in self.children)

    def serialized(self):
        out = super(SetNode, self).serialized()
        out['head'] = self.head.serialized()
        return out



type_inheritances = (
    ('root', 'boolean'),
    ('root', 'number'),
    ('root', 'entity'),
    ('entity', 'point'),
    ('entity', 'oned'),
    ('boolean', 'truth'),
    ('boolean', 'cc'),
    ('boolean', 'is'),
    ('oned', 'line'),
    ('entity', 'angle'),
    ('oned', 'arc'),
    ('entity', 'twod'),
    ('entity', 'angular'),
    ('angular', 'angle'),
    ('angular', 'arc'),
    ('twod', 'polygon'),
    ('twod', 'circle'),
    ('polygon', 'triangle'),
    ('polygon', 'quad'),
    ('polygon', 'hexagon'),
    ('twod', 'sector'),
)

high_order_type_inheritances = (
    ('square', 'quad', 'IsSquare'),
    ('para', 'quad', 'IsParallelogram'),
    ('trapezoid', 'quad', 'IsTrapezoid'),
    ('rectangle', 'quad', 'IsRectangle'),
    ('rhombus', 'quad', 'IsRhombus'),
    ('hypotenuse', 'line', 'IsHypotenuseOf'),
    ('tangent', 'line', 'Tangent'),
    ('secant', 'line', 'Secant'),
    ('midpoint', 'point', 'IsMidpointOf'),
    ('bisector', 'line', 'BisectsAngle'),
    ('side', 'line', 'IsSideOf'),
)

types = set().union(*[set(inheritance) for inheritance in type_inheritances])

type_graph = nx.DiGraph()
for parent, child in type_inheritances:
    type_graph.add_edge(parent, child)
for child, parent, _ in high_order_type_inheritances:
    type_graph.add_edge(parent, child)


def issubtype(child_type, parent_type):
    if child_type == "ground":
        return True
    if parent_type == "ground":
        return False
    if parent_type.startswith("*"):
        parent_type = parent_type[1:]
    if is_plural(child_type):
        child_type = child_type[:-1]
    if is_plural(parent_type):
        parent_type = parent_type[:-1]
    if child_type not in type_graph.nodes() or parent_type not in type_graph.nodes():
        return False
    return nx.has_path(type_graph, parent_type, child_type)

def is_singular(type_):
    return type_ in types

def is_plural(type_):
    return type_ != 'is' and type_[:-1] in types and type_[-1] == 's'

function_signature_tuples = (
    ('Not', 'truth', ['truth']),
    ('True', 'truth', ['truth']),
    ('IsLine', 'truth', ['line']),
    ('IsPoint', 'truth', ['point']),
    ('IsCircle', 'truth', ['circle']),
    ('IsTriangle', 'truth', ['triangle']),
    ('IsQuad', 'truth', ['quad']),
    ('IsRectangle', 'truth', ['quad']),
    ('IsTrapezoid', 'truth', ['quad']),
    ('IsPolygon', 'truth', ['polygon']),
    ('IsRegular', 'truth', ['polygon']),
    ('Point', 'point', ['number', 'number']),
    ('Line', 'line', ['point', 'point'], None, True),
    ('Arc', 'arc', ['circle', 'point', 'point']),
    ('Circle', 'line', ['point', 'number']),
    ('Angle', 'angle', ['point', 'point', 'point']),
    ('Triangle', 'triangle', ['point', 'point', 'point']),
    ('Quad', 'quad', ['point', 'point', 'point', 'point']),
    ('Arc', 'arc', ['circle', 'point', 'point']),
    ('Polygon', 'polygon', ['*point']),
    ('Hexagon', 'hexagon', ['point', 'point', 'point', 'point', 'point', 'point']),
    ('IntersectionOf', 'point', ['entity', 'entity'], None, True),
    ('Is', 'is', ['root', 'root'], None, True),
    ('Equals', 'truth', ['number', 'number']),
    ('Add', 'number', ['number', 'number'], None, True),
    ('Mul', 'number', ['number', 'number'], None, True),
    ('Sub', 'number', ['number', 'number']),
    ('Div', 'number', ['number', 'number']),
    ('Pow', 'number', ['number', 'number']),
    ('Ge', 'truth', ['number', 'number']),
    ('What', 'number', []),
    ('ValueOf', 'number', ['number']),
    ('IsInscribedIn', 'truth', ['polygon', 'circle']),
    ('IsCenterOf', 'truth', ['point', 'twod']),
    ('IsDiameterLineOf', 'truth', ['line', 'circle']),
    ('IsAngle', 'truth', ['angle']),
    ('IsSector', 'truth', ['sector']),
    ('Equilateral', 'truth', ['triangle']),
    ('Isosceles', 'truth', ['triangle']),
    ('IsSquare', 'truth', ['quad']),
    ('IsRightTriangle', 'truth', ['triangle']),
    ('IsRightAngle', 'truth', ['angle']),
    ('AreaOf', 'number', ['twod']),
    ('IsAreaOf', 'truth', ['number', 'twod']),
    ('IsLengthOf', 'truth', ['number', 'oned']),
    ('IsRectLengthOf', 'truth', ['number', 'quad']),
    ('IsDiameterNumOf', 'truth', ['number', 'circle']),
    ('IsSideOf', 'truth', ['number', 'quad']),
    ('SideOf', 'number', ['square']),
    ('PerimeterOf', 'number', ['polygon']),
    ('IsMidpointOf', 'truth', ['point', 'line']),
    ('IsWidthOf', 'truth', ['number', 'quad']),
    ('LengthOf', 'number', ['oned']),
    ('SquaredLengthOf', 'number', ['oned']),
    ('CC', 'cc', ['root', 'root'], None, True),
    ('MeasureOf', 'number', ['angular']),
    ('Perpendicular', 'truth', ['line', 'line'], None, True),
    ('IsChordOf', 'truth', ['line', 'circle']),
    ('Tangent', 'truth', ['line', 'twod']),
    ('Secant', 'truth', ['line', 'circle']),
    ('RadiusOf', 'number', ['circle']),
    ('DiameterOf', 'number', ['circle']),
    ('IsRadiusNumOf', 'truth', ['number', 'circle']),
    ('IsRadiusLineOf', 'truth', ['line', 'circle']),
    ('PointLiesOnLine', 'truth', ['point', 'line']),
    ('PointLiesOnCircle', 'truth', ['point', 'circle']),
    ('Sqrt', 'number', ['number']),
    ('Parallel', 'truth', ['line', 'line'], None, True),
    ('IntersectAt', 'truth', ['*line', 'point']),
    ('Two', 'truth', ['*entity']),
    ('Three', 'truth', ['*entity']),
    ('Five', 'truth', ['*entity']),
    ('Six', 'truth', ['*entity']),
    ('BisectsAngle', 'truth', ['line', 'angle']),
    ('What', 'number', []),
    ('AverageOf', 'number', ['*number']),
    ('SumOf', 'number', ['*number']),
    ('Twice', 'number', ['number']),
    ('RatioOf', 'number', ['number', 'number']),
    ('Integral', 'truth', ['number']),
    ('SquareOf', 'number', ['number']),
    ('Degree', 'number', []),
    ('Pi', 'number', []),
    ('IsSideOf', 'truth', ['line', 'polygon']),
    ('IsHypotenuseOf', 'truth', ['line', 'triangle']),
    ('Congruent', 'truth', ['entity', 'entity']),
    ('Find', 'truth', ['number']),
    ('Measures', 'truth', ['angle', 'number']),
    ('IsGreatest', 'truth', ['*number']),
    ('IsArc', 'truth', ['arc']),
    ('IsAltitudeOf', 'truth', ['line', 'triangle']),
    ('HeightOf', 'number', ['polygon']),
    ('CircumferenceOf', 'number', ['circle']),
    ('HalfOf', 'number', ['number']),
    ('DegreeUnit', 'number', ['number']),
    ('WidthOf', 'number', ['quad']),
    ('IsRhombus', 'truth', ['quad']),
)

abbreviations = {
    '+': 'Add',
    '-': 'Sub',
    '*': 'Mul',
    '/': 'Div',
    ':': 'Div',
    '=': 'Equals',
    '<': 'Ge',
    '^': 'Pow',
    r'\sqrt': 'Sqrt',
    r'\pi': 'Pi',
    r'\none': 'None',
    r'\degree': 'Degree',
    r'\what': 'What',
    '||': 'Parallel',
}

def get_function_signatures():
    local_function_signatures = {}
    for tuple_ in function_signature_tuples:
        if len(tuple_) == 3:
            id_, return_type, arg_types = tuple_
            function_signature = FunctionSignature(id_, return_type, arg_types)
        elif len(tuple_) == 5:
            id_, return_type, arg_types, arg_pluralities, is_symmetric = tuple_
            function_signature = FunctionSignature(id_, return_type, arg_types, arg_pluralities, is_symmetric)
        local_function_signatures[id_] = function_signature
    return local_function_signatures

signatures = get_function_signatures()
signatures['What'] = VariableSignature('What', 'number')
signatures['Which'] = VariableSignature('Which', 'ground')
signatures['Except'] = VariableSignature('Except', 'ground')
#signatures['Following'] = VariableSignature('Following', 'ground')