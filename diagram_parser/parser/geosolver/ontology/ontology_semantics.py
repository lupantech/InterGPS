import numpy as np
from functools import reduce

import itertools
from geosolver.diagram.computational_geometry import distance_between_line_and_point, line_length, \
    distance_between_points, angle_in_radian, cartesian_angle, signed_distance_between_cartesian_angles, \
    horizontal_angle, area_of_polygon, distance_between_points_squared, perpendicular_distance_between_line_and_point
from geosolver.ontology.instantiator_definitions import instantiators
from geosolver.ontology.ontology_definitions import FormulaNode, VariableSignature, issubtype, SetNode, Node
import sys
from geosolver.utils.num import is_number
import operator

this = sys.modules[__name__]

__author__ = 'minjoon'

class TruthValue(object):
    def __init__(self, norm, std=1.0, conf=None):
        assert norm >= 0
        self.norm = norm
        if conf is None:
            self.conf = max(0, 1-norm/std)
        else:
            self.conf = conf

    def __and__(self, other):
        if isinstance(other, TruthValue):
            conf = self.conf
            if self.conf > other.conf:
                conf = other.conf
            norm = (self.norm + other.norm)/2.0
            return TruthValue(norm, conf=conf)
        elif other is True:
            return self
        else:
            raise Exception()

    def __or__(self, other):
        if isinstance(other, TruthValue):
            conf = self.conf
            if self.conf < other.conf:
                conf = other.conf
            norm = np.sqrt(self.norm * other.norm)
            return TruthValue(norm, conf=conf)
        elif other is False:
            return self
        else:
            raise Exception()

    def __rand__(self, other):
        return self.__and__(other)

    def __ror__(self, other):
        return self.__or__(other)

    def flip(self):
        if self.norm == 0:
            norm = 10**5
        else:
            norm = 1.0/self.norm
        conf = 1-self.conf
        out = TruthValue(norm, conf=conf)
        return out

    def __repr__(self):
        return "TV(norm=%.3f, conf=%.2f)" % (self.norm, self.conf)

def Line(p1, p2):
    return instantiators['line'](p1, p2)

def Arc(circle, p1, p2):
    return instantiators['arc'](circle, p1, p2)

def Circle(p, r):
    return instantiators['circle'](p, r)

def Point(x, y):
    return instantiators['point'](x, y)

def Angle(a, b, c):
    return instantiators['angle'](a, b, c)

def Triangle(a, b, c):
    return instantiators['triangle'](a, b, c)

def Quad(a, b, c, d):
    return instantiators['quad'](a, b, c, d)

def Hexagon(a, b, c, d, e, f):
    return instantiators['polygon'](a, b, c, d, e, f)

def Polygon(*p):
    return instantiators['polygon'](*p)

def LengthOf(twod):
    if isinstance(twod, instantiators['line']):
        return line_length(twod)
    elif isinstance(twod, instantiators['arc']):
        circle, a, b = twod
        return circle.radius*(b-a)

def SquaredLengthOf(line):
    return distance_between_points_squared(*line)

def RadiusOf(circle):
    return circle.radius

def IsRadiusNumOf(number, circle):
    return Equals(number, RadiusOf(circle))

def IsRadiusLineOf(line, circle):
    if line[0] != circle.center and line[1] != circle.center:
        return TruthValue(np.inf)
    return PointLiesOnCircle(line[0], circle) | PointLiesOnCircle(line[1], circle)

def LineIsLine(l0, l1):
    if frozenset(l0) == frozenset(l1):
        return TruthValue(0)
    return TruthValue(np.inf)

def IsSideOf(line, polygon):
    for each in _polygon_to_lines(polygon):
        if LineIsLine(line, each):
            return TruthValue(0)
    return TruthValue(np.inf)

def IsHypotenuseOf(line, triangle):
    lines = _polygon_to_lines(triangle)
    longest_line = max(lines, key=lambda l: LengthOf(l))
    return LineIsLine(line, longest_line)

def Congruent(a, b):
    if isinstance(a, instantiators['line']):
        return Equals(LengthOf(a), LengthOf(b))
    elif isinstance(a, instantiators['angle']):
        return Equals(MeasureOf(a), MeasureOf(b))

def Equals(a, b):
    std = abs((a+b)/2.0)
    value = abs(a-b)
    out = TruthValue(value, std)
    return out

def Ge(a, b):
    std = abs((a+b)/2.0)
    value = max(0, b-a)
    out = TruthValue(value, std)
    return out

def Sqrt(x):
    return np.sqrt(x)

def Add(a, b):
    return a + b

def Sub(a, b):
    return a - b

def Mul(a, b):
    return a * b

def Div(a, b):
    return float(a) / b

def RatioOf(a, b):
    return Div(a, b)

def Pow(a, b):
    return a**b

def Or(a, b):
    if a.conf > b.conf:
        return a
    return b

def Tangent(line, twod):
    name = twod.__class__.__name__
    if name == "circle":
        d = perpendicular_distance_between_line_and_point(line, twod.center)
        return Equals(d, twod.radius)
    elif issubtype(name, 'polygon'):
        out = reduce(operator.__or__, (PointLiesOnLine(point, line) for point in twod), False)
        return out
    raise Exception()

def Secant(line, circle):
    d = distance_between_line_and_point(line, circle.center)
    return Ge(circle.radius, d)

def IsDiameterLineOf(line, circle):
    return IsChordOf(line, circle) & Equals(LengthOf(line), 2*circle.radius)

def DiameterOf(circle):
    return 2*circle.radius

def PointLiesOnCircle(point, circle):
    d = distance_between_points(point, circle.center)
    return Equals(d, circle.radius)

def IsChordOf(line, circle):
    return PointLiesOnCircle(line.a, circle) & PointLiesOnCircle(line.b, circle)

def IsAltitudeOf(line, triangle):
    a, b = line
    if a in triangle:
        ix = a
    elif b in triangle:
        ix = b
    else:
        return TruthValue(np.inf)
    base = instantiators['line'](*set(triangle).difference([ix]))
    return Perpendicular(line, base)

def Perpendicular(l0, l1):
    # return Equals((l0.b.y-l0.a.y)*(l1.b.y-l1.a.y), (l0.a.x-l0.b.x)*(l1.b.x-l1.a.x))
    a0 = cartesian_angle(*l0)
    a1 = cartesian_angle(*l1)
    da = horizontal_angle(signed_distance_between_cartesian_angles(a0, a1))
    return Equals(da, np.pi/2)

def Colinear(A, B, C):
    line = instantiators['line'](A, C)
    eq = Equals(LengthOf(line), distance_between_points(line.a, B) + distance_between_points(line.b, B))
    return eq

def PointLiesOnLine(point, line):
    angle = instantiators['angle'](line[0], point, line[1])
    return Equals(MeasureOf(angle), np.pi)
    #return Colinear(line[0], point, line[1])

def IsMidpointOf(point, line):
    line_a = Line(line.a, point)
    line_b = Line(point, line.b)
    e = Equals(LengthOf(line_a), LengthOf(line_b))
    l = PointLiesOnLine(point, line)
    return e & l

def IsTriangle(triangle):
    if isinstance(triangle, instantiators['triangle']):
        return TruthValue(0)
    else:
        return TruthValue(np.inf)

def IsLine(line):
    if isinstance(line, instantiators['line']):
        return TruthValue(0)
    else:
        return TruthValue(np.inf)

def IsAngle(angle):
    if isinstance(angle, instantiators['angle']):
        return TruthValue(0)
    else:
        return TruthValue(np.inf)

def IsPoint(point):
    if isinstance(point, instantiators['point']):
        return TruthValue(0)
    else:
        return TruthValue(np.inf)

def IsQuad(quad):
    if quad.__class__.__name__ == 'quad':
        return TruthValue(0)
    return TruthValue(np.inf)

def IsInscribedIn(triangle, circle):
    out = reduce(operator.__and__, (PointLiesOnCircle(point, circle) for point in triangle), True)
    return out

def IsCenterOf(point, twod):
    name = twod.__class__.__name__
    if name == 'circle':
        return Equals(point[0], twod.center[0]) & Equals(point[1], twod.center[1])
    elif issubtype(name, 'polygon'):
        distances = [distance_between_points(point, each) for each in twod]
        reg = IsRegular(twod)
        out = reduce(operator.__and__, (Equals(distances[index-1], distance) for index, distance in enumerate(distances)), True)
        return reg & out
    else:
        raise Exception()

def IntersectAt(lines, point):
    assert isinstance(lines, SetNode)
    out = reduce(operator.__and__, (PointLiesOnLine(point, line) for line in lines.children), True)
    return out

def Equilateral(triangle):
    lines = [instantiators['line'](triangle[index-1], point) for index, point in enumerate(triangle)]
    return Equals(LengthOf(lines[0]), LengthOf(lines[1])) & Equals(LengthOf(lines[1]), LengthOf(lines[2]))

def IsRhombus(quad):
    lines = [instantiators['line'](quad[index-1], point) for index, point in enumerate(quad)]
    return Equals(LengthOf(lines[0]), LengthOf(lines[1])) & \
           Equals(LengthOf(lines[1]), LengthOf(lines[2])) & Equals(LengthOf(lines[2]), LengthOf(lines[3]))

def IsSquare(quad):
    return IsRegular(quad)

def AreaOf(twod):
    name = twod.__class__.__name__
    assert issubtype(name, 'twod')
    if name == "circle":
        center, radius = twod
        area = np.pi * radius ** 2
    elif issubtype(name, 'polygon'):
        # http://mathworld.wolfram.com/PolygonArea.html
        area = area_of_polygon(twod)
    elif name == 'arc':
        circle, a, b = twod
    else:
        raise Exception()
    return area

def MeasureOf(x):
    if isinstance(x, instantiators['angle']):
        return angle_in_radian(x, False)
    elif isinstance(x, instantiators['arc']):
        circle, a, b = x
        angle = Angle(a, circle.center, b)
        return angle_in_radian(angle, False)

def Measures(angle, number):
    return Equals(MeasureOf(angle), number)

def IsAreaOf(number, twod):
    return Equals(number, AreaOf(twod))

def IsLengthOf(number, line):
    return Equals(number, LengthOf(line))

def IsPolygon(polygon):
    return TruthValue(0)

def Isosceles(triangle):
    sides = [distance_between_points(triangle[index-1], point) for index, point in enumerate(triangle)]
    combs = itertools.combinations(sides, 2)

    out = reduce(operator.__or__, (Equals(a, b) for a, b in combs), False)
    return out

def IsArc(arc):
    if isinstance(arc, instantiators['arc']):
        return TruthValue(0)
    return TruthValue(np.inf)

def BisectsAngle(line, angle):
    distant_point = line[0]
    if distant_point == angle[1]:
        distant_point = line[1]
    a0 = instantiators['angle'](angle[0], angle[1], distant_point)
    a1 = instantiators['angle'](distant_point, angle[1], angle[2])
    eq = Equals(MeasureOf(a0), MeasureOf(a1))
    return eq

def Three(entities):
    if len(entities.children) == 3:
        return TruthValue(0)
    return TruthValue(np.inf)

def Two(entities):
    if len(entities.children) == 2:
        return TruthValue(0)
    return TruthValue(np.inf)

def Five(entities):
    if not isinstance(entities, SetNode):
        return TruthValue(np.inf)
    if len(entities.children) == 5:
        return TruthValue(0)
    return TruthValue(np.inf)

def Six(entities):
    if len(entities.children) == 6:
        return TruthValue(0)
    return TruthValue(np.inf)

def Not(truth):
    return truth.flip()

def DegreeUnit(number):
    return Mul(number, Degree())


def SumOf(set_node):
    assert isinstance(set_node,SetNode)
    return sum(child for child in set_node.children)

def Parallel(line_0, line_1):
    a0 = cartesian_angle(*line_0)
    a1 = cartesian_angle(*line_1)+np.pi/2
    da = horizontal_angle(signed_distance_between_cartesian_angles(a0, a1))
    return Equals(da, np.pi/2)

def IsTrapezoid(quad):
    lines = _polygon_to_lines(quad)
    out = Parallel(lines[0], lines[2]) | Parallel(lines[1], lines[3])
    return out

def IsRegular(polygon):
    lines = _polygon_to_lines(polygon)
    l = reduce(operator.__and__, (Equals(LengthOf(lines[index-1]), LengthOf(line)) for index, line in enumerate(lines)), True)
    angles = _polygon_to_angles(polygon)
    ans = np.pi*(len(polygon)-2)/len(polygon)
    a = reduce(operator.__and__, (Equals(MeasureOf(angle), ans) for angle in angles), True)
    return a & l

def IsRectangle(quad):
    lines = _polygon_to_lines(quad)
    out = reduce(operator.__and__, (Perpendicular(lines[index-1], line) for index, line in enumerate(lines)), True)
    return out

def ValueOf(number):
    return number

def AverageOf(set_node):
    return np.mean(set_node.children)

def PerimeterOf(polygon):
    lines = _polygon_to_lines(polygon)
    return sum(LengthOf(line) for line in lines)

def SquareOf(number):
    return number ** 2

def IsRightTriangle(triangle):
    angles = _polygon_to_angles(triangle)
    tv = reduce(operator.__or__, (IsRightAngle(angle) for angle in angles), False)
    return tv

def IsRightAngle(angle):
    return Equals(np.pi/2, MeasureOf(angle))

def Find(number):
    return TruthValue(0)

def IsRectLengthOf(number, quad):
    l1 = distance_between_points(quad[0], quad[1])
    l2 = distance_between_points(quad[1], quad[2])
    return Equals(l1, number) | Equals(l2, number)

def Is(a, b):
    if is_number(a) or is_number(b):
        return Equals(a, b)

    a_name = a.__class__.__name__
    b_name = b.__class__.__name__
    if issubtype(a_name , 'polygon') or issubtype(a_name, 'line'):
        truth = set(a) == set(b)
    else:
        truth = a == b

    if truth:
        return TruthValue(0)
    else:
        return TruthValue(np.inf)



def Pi():
    return np.pi

def Degree():
    return np.pi/180

def isTrue(tv):
    return tv

def IsCircle(circle):
    if isinstance(circle, instantiators['circle']):
        return TruthValue(0)
    return TruthValue(np.inf)

def _polygon_to_lines(polygon):
    return [Line(polygon[index-1], point) for index, point in enumerate(polygon)]

def _polygon_to_angles(polygon):
    return [Angle(polygon[index-2], polygon[index-1], point) for index, point in enumerate(polygon)]

def evaluate(formula, assignment):
    if not isinstance(formula, Node):
        return formula
    if not formula.is_grounded(assignment.keys()):
        return None

    if isinstance(formula, SetNode):
        if issubtype(formula.head.return_type, 'boolean'):
            out = reduce(operator.__and__, (evaluate(child, assignment) for child in formula.children), True)
            return out
        return formula

    if isinstance(formula.signature, VariableSignature):
        return assignment[formula.signature.id]
    elif is_number(formula.signature.id):
        return float(formula.signature.id)
    else:
        evaluated_args = []
        for arg in formula.children:
            if isinstance(arg, FormulaNode):
                evaluated_args.append(evaluate(arg, assignment))
            elif isinstance(arg, SetNode):
                evaluated_args.append(SetNode([evaluate(arg_arg, assignment) for arg_arg in arg.children]))
            else:
                evaluated_args.append(arg)
        # FIXME : rather than try/catch, check type matching
        try:
            out = getattr(this, formula.signature.id)(*evaluated_args)
            return out
        except:
            return TruthValue(np.inf)

