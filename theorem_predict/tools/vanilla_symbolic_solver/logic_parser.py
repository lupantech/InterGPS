from nltk import Tree

import re, operator
from pyparsing import OneOrMore, Optional, Word, quotedString, delimitedList, Suppress, alphanums, alphas, Forward, Group, Word, Literal, Combine, ZeroOrMore, nums


from basic_definition import BasicDefinition
from extended_definition import ExtendedDefinition

from sympy.parsing.sympy_parser import parse_expr,standard_transformations, implicit_multiplication_application
from sympy.parsing.latex import parse_latex
from sympy import Symbol

from itertools import permutations, product, combinations
from sympy import  cos, sin, tan, cot, sqrt, pi, acos, asin, solve

from kanren import Relation, facts
from kanren import run, eq, membero, var, conde

import math
import time

from utils import heron_triangle_formula, angle_area_formula


class LogicParser():
    def __init__(self, logic):
        assert isinstance(logic, ExtendedDefinition)
        self.logic = logic
        self.expression = Forward()

        identifier = Word(alphanums + ' +-*/.\\\{\}^_$\'')
        # integer  = Word( nums )
        lparen = Literal("(").suppress() # suppress "(" in the result
        rparen = Literal(")").suppress() # suppress ")" in the result

        arg = Group(self.expression) | identifier # arg can be a grouping expression or a identifier
        args = arg + ZeroOrMore( Literal(",").suppress() + arg) # args: arg1, [*arg2, *arg3, ...]

        self.expression <<= identifier + lparen + Optional(args)  + rparen # args is optional
    
    def parse(self, tree):
        parseResult =  self.expression.parseString(tree)
        return parseResult
    
    def EvaluateSymbols(self, tree):
        a = parse_expr(tree, transformations=(standard_transformations + (implicit_multiplication_application,)))
        return a
    
    def getValue(self, expr, val = None):
        '''
        Give an expression [expr].
        You should output its value if [val = None], otherwise execute [expr := val].
        '''
        if type(expr) == str:
            if val != None:
                self.logic.define_equal(Symbol(expr), val)
            else:
                if expr.find("angle") != -1: # 'angle_1'
                    return Symbol(expr)
                try:
                    import sys
                    savedStdout = sys.stdout
                    sys.stdout = None # close the stdout to mute the warning information
                    val = parse_latex(expr).evalf() # evaluate the latex expression to a numerical value
                    sys.stdout = savedStdout # open the stdout
                    return val
                except:
                    return self.EvaluateSymbols(expr) # special case: convert the expression to a symbol

        # Some logic forms may miss these phrases.
        if expr[0] == "Line":
            expr = ["LengthOf", expr]
        if expr[0] in ["Angle", "Arc"]:
            expr = ["MeasureOf", expr]

        if expr[0] == "MeasureOf":
            if type(expr[1]) == str:
                if val == None:
                    return Symbol(expr[1])
                self.logic.define_equal(val, Symbol(expr[1]))

            if expr[1][0] == "Angle":
                if len(expr[1]) == 2 and expr[1][1].isdigit():
                    # MeasureOf(Angle(1)), expr = ['MeasureOf', ['Angle', 1]]
                    angle_value = Symbol("angle " + str(expr[1][1])) # {Symbol} angle_ABC
                    if val == None:
                        return angle_value
                    self.logic.define_equal(angle_value, val)
                else:
                    # MeasureOf(Angle(A,B,C)), expr = ['MeasureOf', ['Angle', 'A', 'B', 'C']]
                    angle = self.logic.parseAngle(expr[1][1:]) # ['A', 'B', 'C']
                    if val != None:
                        self.logic.defineAngle(*angle, val) # val = 2.0*angle_ADC, 83.00, 8.0*y + 2.0
                    else:
                        try:
                            angle_value = self.logic.find_angle_measure(angle)[0]
                            return angle_value
                        except:
                            angle_value = self.logic.newAngleSymbol(angle) # {Symbol} angle_ABC
                            return angle_value

            if expr[1][0] == "Arc":
                arc = self.logic.parseArc(expr[1][1:])
                if val != None:
                    self.logic.defineArc(*arc, val)
                else:
                    try:
                        return self.logic.find_arc_measure(arc)[0]
                    except:
                        return self.logic.newArcSymbol(arc)

        if expr[0] == "LengthOf":
            # ['LengthOf', ['Line', 'B', 'C']]
            if expr[1][0] == "Line":
                line = expr[1][1:]
                if val != None:
                    self.logic.defineLine(*line, val)
                else:
                    try:
                        length = self.logic.find_line_with_length(line)[0] # 'line_CA', 'x', 'line_CA+x'
                        return length
                    except:
                        length = self.logic.newLineSymbol(line)
                        return length  # {Symbol} line_CA
            # Assume there is no LengthOf(Arc())

        if expr[0] in ["SinOf", "CosOf", "TanOf", "CotOf"]:
            if expr[1][0] == "Angle":
                # In this case, 'MeasureOf' may be skipped.
                expr[1] = ['MeasureOf', expr[1]]
            
            mp = {"SinOf": sin, "CosOf": cos, "TanOf": tan, "CotOf": cot}
            return mp[expr[0]](self.getValue(expr[1]))
        
        if expr[0] in ["Add", "Mul", "SumOf", "HalfOf", "SquareOf", "SqrtOf"]:
            if expr[0] == "HalfOf": return self.getValue(expr[1]) / 2.0
            if expr[0] == "SquareOf": return self.getValue(expr[1]) ** 2
            if expr[0] == "SqrtOf": return self.getValue(expr[1]) ** 0.5
            if expr[0] in ["Add", "SumOf"]: return sum([self.getValue(x) for x in expr[1:]])
            ret = 1             # Mul
            for x in expr[1:]:
                ret *= self.getValue(x)
            return ret

    def parseQuad(self, tree):
        # tree = ['Rhombus', 'A', 'B', 'C', 'D']
        identifier = tree[0]
        if len(tree) == 2 and tree[1] == "$":
            polygon = self.logic.find_hidden_polygons(4)
            if len(polygon) != 1:
                return
            tree[1:] = polygon[0]
        
        if identifier in ["Quadrilateral", "Trapezoid"]:
            self.logic.definePolygon(tree[1:])
        if identifier == "Trapezoid":
            if self.logic.point_positions != None:
                p = [self.logic.point_positions[x] for x in tree[1:]]
                cross = lambda u, v: u[0]*v[1]-u[1]*v[0]
                c1 = cross((p[1][0]-p[0][0], p[1][1]-p[0][1]), (p[2][0]-p[3][0], p[2][0]-p[3][1]))
                c2 = cross((p[3][0]-p[0][0], p[3][1]-p[0][1]), (p[2][0]-p[1][0], p[2][0]-p[1][1]))
                if abs(c1) < abs(c2):
                    self.Parallel(['Line', tree[1], tree[2]], ['Line', tree[3], tree[4]])
                else:
                    self.Parallel(['Line', tree[2], tree[3]], ['Line', tree[4], tree[1]])
        if identifier == "Rhombus":
            self.logic.definePolygon(tree[1:])
            self.Parallel(['Line', tree[1], tree[2]], ['Line', tree[4], tree[3]])
            self.Parallel(['Line', tree[2], tree[3]], ['Line', tree[1], tree[4]])
            self.Perpendicular(['Line', tree[1], tree[3]], ['Line', tree[2], tree[4]], True)
            for ch in range(1, 4):
                self.logic.lineEqual([tree[ch], tree[ch+1]], [tree[ch+1], tree[(ch+1)%4+1]])
        if identifier == "Parallelogram":
            self.logic.definePolygon(tree[1:])
            self.Parallel(['Line', tree[1], tree[2]], ['Line', tree[4], tree[3]])
            self.Parallel(['Line', tree[2], tree[3]], ['Line', tree[1], tree[4]])
            self.logic.lineEqual([tree[1], tree[2]], [tree[4], tree[3]])
            self.logic.lineEqual([tree[2], tree[3]], [tree[1], tree[4]])
        if identifier in ["Rectangle", "Square"]:
            self.logic.definePolygon(tree[1:])
            self.Parallel(['Line', tree[1], tree[2]], ['Line', tree[4], tree[3]])
            self.Parallel(['Line', tree[2], tree[3]], ['Line', tree[1], tree[4]])
            self.Perpendicular(['Line', tree[1], tree[2]], ['Line', tree[2], tree[3]])
            self.Perpendicular(['Line', tree[2], tree[3]], ['Line', tree[3], tree[4]])
            self.logic.lineEqual([tree[1], tree[2]], [tree[4], tree[3]])
            self.logic.lineEqual([tree[2], tree[3]], [tree[1], tree[4]])
        if identifier == "Square":
            self.logic.definePolygon(tree[1:])
            self.Parallel(['Line', tree[1], tree[2]], ['Line', tree[4], tree[3]])
            self.Parallel(['Line', tree[2], tree[3]], ['Line', tree[1], tree[4]])
            self.Perpendicular(['Line', tree[1], tree[3]], ['Line', tree[2], tree[4]])
            for ch in range(1, 4):
                self.logic.lineEqual([tree[ch], tree[ch+1]], [tree[ch+1], tree[(ch+1)%4+1]])
        if identifier == "Kite":
            self.logic.definePolygon(tree[1:])
            self.Perpendicular(['Line', tree[1], tree[3]], ['Line', tree[2], tree[4]])
            if self.logic.point_positions != None:
                fp = lambda x: self.logic.point_positions[x]
                p1, p2, p3, p4 = fp(tree[1]), fp(tree[2]), fp(tree[3]), fp(tree[4])
                fdis = lambda x, y: ((x[0] - y[0]) ** 2 + (x[1] - y[1]) ** 2) ** 0.5
                if abs(fdis(p1, p2) - fdis(p2, p3)) < abs(fdis(p2, p3) - fdis(p3, p4)):
                    self.logic.lineEqual([tree[1], tree[2]], [tree[2], tree[3]])
                    self.logic.lineEqual([tree[3], tree[4]], [tree[4], tree[1]])
                else:
                    self.logic.lineEqual([tree[2], tree[3]], [tree[3], tree[4]])
                    self.logic.lineEqual([tree[4], tree[1]], [tree[1], tree[2]])      

    def PointLiesOnLine(self, point, line):
        line = self.logic.parseLine(line[1:])
        if line != None:
            self.logic.defineLine(*line)
            self.logic.defineAngle(line[0], point, line[1], 180)

    def PointLiesOnCircle(self, point, circle):
        assert circle[0] == "Circle"
        if circle[1] == "$":
            circle[1] = self.logic.find_all_circles()[0]
        self.logic.defineCircle(circle[1], point)

    def Perpendicular(self, line1, line2, build_new_point = False):
        # Perpendicular should be put into the last.
        # Because if we know Line(A, B) = Line(C, D), we can not get the intersection easily.
        self.logic.defineLine(line1[1], line1[2])
        self.logic.defineLine(line2[1], line2[2])
        # print (line1, line2)
        s1 = set(self.logic.find_all_points_on_line(line1[1:]))
        s2 = set(self.logic.find_all_points_on_line(line2[1:]))
        if  len(s1 & s2) != 1:
            #print ("The perpendicular lines", line1, line2, "should have one intersection.")
            return
        intersection = (s1&s2).pop()
        for point1 in s1-s2:
            for point2 in s2-s1:
                self.logic.defineAngle(point1, intersection, point2, 90)
                self.logic.defineAngle(point2, intersection, point1, 90)
    
    def Parallel(self, line1, line2):
        line1 = self.logic.parseLine(line1[1:])
        line2 = self.logic.parseLine(line2[1:])
        if line1 != None and line2 != None:
            #print (line1, line2)
            self.logic.defineLine(*line1)
            self.logic.defineLine(*line2)
            self.logic.define_parallel(line1, line2)

    def LegOf(self, expr):
        pass
    
    def BisectsAngle(self, line, angle):
        if line[1] != angle[2]:
            line[1], line[2] = line[2], line[1]
        self.logic.angleEqual([angle[1], angle[2], line[2]], [angle[3], angle[2], line[2]])

    def Midpoint(self, point, line):
        line = self.logic.parseLine(line, point)
        self.logic.lineEqual([line[0], point], [line[1], point])
        self.logic.defineAngle(line[0], point, line[1], 180)

    def dfsParseTree(self, tree):
        identifier = tree[0]

        ''' 1. Geometric Shapes '''
        if identifier == "Angle":
            if len(tree) == 4:
                self.logic.defineAngle(tree[1], tree[2], tree[3])
        if identifier == "Line":
            self.logic.defineLine(tree[1], tree[2])
        if identifier in ["Quadrilateral", "Parallelogram", "Rhombus", "Rectangle", "Square", "Trapezoid", "Kite"]:
            self.parseQuad(tree)
        if identifier == "Polygon":
            self.logic.definePolygon(tree[1:])

        ''' 2. Unary Geometric Attributes '''
        if identifier == "Equilateral" and tree[1][0] == "Triangle":
            a, b, c = tree[1][1:]
            self.logic.lineEqual([a, b], [b, c])
            self.logic.lineEqual([a, b], [a, c])
            self.logic.defineAngle(a, b, c, 60)
            self.logic.defineAngle(b, a, c, 60)
            self.logic.defineAngle(a, c, b, 60)

        if identifier == "Isosceles" and tree[1][0] == "Triangle":
            if self.logic.point_positions != None:
                points = tree[1][1:] 
                positions = [self.logic.point_positions[x] for x in points]
                fdis = lambda x, y: ((x[0] - y[0]) ** 2 + (x[1] - y[1]) ** 2) ** 0.5
                mindis, minid = 999999, -1
                for i in range(3):
                    nowdis = abs(fdis(positions[i], positions[1 - min(i, 1)]) - fdis(positions[i], positions[3 - max(1, i)]))
                    if nowdis < mindis:
                        mindis, minid = nowdis, i
                o, p, q = points[minid], points[1 - min(minid, 1)], points[3 - max(minid, 1)]
                self.logic.lineEqual([o, p], [o, q])
                self.logic.angleEqual([o, p, q], [o, q, p])
        
        ''' 4. Binary Geometric Relations '''
        if identifier == "PointLiesOnLine":
            self.PointLiesOnLine(tree[1], tree[2])
        if identifier == "PointLiesOnCircle":
            self.PointLiesOnCircle(tree[1], tree[2])
        if identifier == "Parallel":
            self.Parallel(tree[1], tree[2])
        if identifier == "Perpendicular":
            self.Perpendicular(tree[1], tree[2])
        if identifier == "IntersectAt":
            if tree[1][0] == "Line":
                for i in range(1, len(tree)-1):
                    self.PointLiesOnLine(tree[-1][1], tree[i])
            elif tree[1][0] == "Circle":
                for i in range(1, len(tree)-1):
                    self.PointLiesOnCircle(tree[-1][1], tree[i])
            else:
                raise RuntimeError("No such format for IntersectAt.")
        if identifier == "BisectsAngle":
            self.BisectsAngle(tree[1], tree[2])
        if identifier == "Congruent":
            if tree[1][0] == "Triangle":
                self.logic.defineCongruentTriangle(tree[1][1:], tree[2][1:])
            # Do not implement the polygon with sides > 3.
        if identifier == "Similar":
            if tree[1][0] == "Triangle":
                self.logic.defineSimilarTriangle(tree[1][1:], tree[2][1:])
            # Do not implement the polygon with sides > 3.
        if identifier in ["Tangent", "Secant", "CircumscribedTo", "InscribedIn"]:
            if identifier == "InscribedIn":
                assert tree[2][0] == "Circle"
                self.dfsParseTree(tree[1])
                for p in tree[1][1:]:
                    self.PointLiesOnCircle(p, tree[2])
                if tree[1][0] in ["Square", "Rectangle"]:
                    self.PointLiesOnLine(tree[2][1], ['Line', tree[1][1], tree[1][3]])
                    self.PointLiesOnLine(tree[2][1], ['Line', tree[1][2], tree[1][4]])
     
        ''' 5. A-IsXOf-B  Geometric Relations '''
        if identifier == "IsMidpointOf":
            # IsMidpointOf(Point, Line/LegOf)
            if tree[2][0] == "Line":
                self.Midpoint(tree[1][1], tree[2][1:])
            elif tree[2][0] == "LegOf":
                self.Midpoint(tree[1][1], self.LegOf(tree[2][1]))
            else:
                raise RuntimeError("No such format for IsMidpointOf.")
        if identifier == "IsCentroidOf":
            o = tree[1][1]
            points = self.logic.find_all_lines_for_point(o)
            if len(tree[2]) == 4:
                # Triangle
                a, b, c = tree[2][1:]
                angles = self.logic.find_all_180_angles()
                for p in points:
                    if (a, p, b) in angles: 
                        self.logic.lineEqual([p, a], [p, b])
                        self.getValue(["LengthOf", ["Line", p, o]], self.getValue(["LengthOf", ["Line", c, o]]) * 2)
                    if (b, p, c) in angles: 
                        self.logic.lineEqual([p, b], [p, c])
                        self.getValue(["LengthOf", ["Line", p, o]], self.getValue(["LengthOf", ["Line", a, o]]) * 2)
                    if (a, p, c) in angles: 
                        self.logic.lineEqual([p, a], [p, c])
                        self.getValue(["LengthOf", ["Line", p, o]], self.getValue(["LengthOf", ["Line", b, o]]) * 2)
                
        if identifier == "IsIncenterOf":
            o = tree[1][1]
            points = self.logic.find_all_lines_for_point(o)
            if len(tree[2]) == 4:
                # Triangle
                a, b, c = tree[2][1:]
                self.logic.angleEqual([b, a, o], [c, a, o])
                self.logic.angleEqual([a, b, o], [c, b, o])
                self.logic.angleEqual([a, c, o], [b, c, o])
        if identifier == "IsRadiusOf":
            if tree[2][1] == tree[1][1]:
                self.PointLiesOnCircle(tree[1][2], tree[2])
            else:
                self.PointLiesOnCircle(tree[1][1], tree[2])
        if identifier == "IsDiameterOf":
            # print (tree[1], tree[2])
            self.PointLiesOnLine(tree[2][1], tree[1])
            self.PointLiesOnCircle(tree[1][1], tree[2])
            self.PointLiesOnCircle(tree[1][2], tree[2])
        if identifier == "IsMidsegmentOf":
            segs = []
            for i in range(1, 3):
                for k in range(1, 4):
                    if self.logic.find_angle_measure([tree[2][k], tree[1][i], tree[2][k%3+1], 180]):
                        segs.append([tree[2][k], tree[2][k%3+1]])
            assert len(segs) == 2, "Find Midsegment Error."
            self.Midpoint(tree[1][1], segs[0])
            self.Midpoint(tree[1][2], segs[1])
            baseline = [x for x in tree[2][1:] if not x in segs[0] or not x in segs[1]]
            assert len(baseline) == 2, "Find Midsegment Error."
            self.Parallel(tree[1][1:], baseline)
        if identifier == "IsChordOf":
            self.PointLiesOnCircle(tree[1][1], tree[2])
            self.PointLiesOnCircle(tree[1][2], tree[2])
        if identifier == "IsDiagonalOf":
            if len(tree[2]) == 5:
                self.parseQuad(tree[2])
        
        '''6. Numerical Attributes and Relations'''
        if identifier == "Equals":
            if tree[1][0] == "RadiusOf":
                O = tree[1][1][1]
                for p in self.logic.find_points_on_circle(O):
                    self.logic.defineLine(O, p, self.EvaluateSymbols(tree[2]))
            else:
                # self.parseEquals(tree[1], tree[2])
                def _totlength(data):
                    if type(data) == list:
                        return sum([_totlength(x) for x in data])
                    return 1
                if _totlength(tree[1]) < _totlength(tree[2]):
                    # Put more complex expression to the left.
                    tree[1], tree[2] = tree[2], tree[1]
                val = self.getValue(tree[2])
                # print (tree[1], tree[2], val)
                self.getValue(tree[1], val)
        
    def _find_angle(self, phrase):
        if len(phrase) == 4:
            return ['Value', *phrase[1:4]]
        elif len(phrase) == 2:
            if phrase[1].isupper():
                return ['Value', *self.logic.parseAngle(phrase[1])]
            return ['Value', "angle " + str(phrase[1])]

    def findTarget(self, phrase):
        ''' 
        Generate the target from the 'Find' phrase.
        The format is defined in 'logic_solver.Search()'.
        '''
        assert phrase[0] == "Find"
        phrase = phrase[1]    

        if type(phrase) == str:
            return ['Value', phrase]
        phrase = list(phrase) # ['LengthOf', ['Line', 'O', 'X']]

        if phrase[0] == "LengthOf":
            phrase = phrase[1]
            if phrase[0] == "Arc":
                return ['Value', 'arc_length', *self.logic.parseArc(phrase[1:])]
            assert phrase[0] == "Line" and len(phrase) == 3
            return ['Value', *phrase[1:3]]
        
        if phrase[0] == "MeasureOf":
            phrase = phrase[1]
            if phrase[0] == "Arc":
                return ['Value', 'arc_measure', *self.logic.parseArc(phrase[1:])]
            elif phrase[0] == "Angle":
                return self._find_angle(phrase)
            return None
        
        if phrase[0] == "PerimeterOf" or phrase[0] == "CircumferenceOf":
            if len(phrase[1]) == 2:
                if phrase[1][0] == 'Circle' and phrase[1][1] == "$":
                    tmp = self.logic.find_all_circles()
                    if len(tmp) > 0:
                        phrase[1][1:] = list(tmp[0])
                elif phrase[1][1] == "$":
                    for i in range(4, 2, -1):
                        tmp = self.logic.find_hidden_polygons(i)
                        if len(tmp) > 0:
                            phrase[1][1:] = list(tmp[0])
                            break
            if len(phrase[1]) == 5:
                self.parseQuad(phrase[1])
            return ['Perimeter', *phrase[1][1:]]
        
        if phrase[0] == "AreaOf":
            if len(phrase[1]) == 2:
                if phrase[1][0] == 'Circle' and phrase[1][1] == "$":
                    tmp = self.logic.find_all_circles()
                    if len(tmp) > 0:
                        phrase[1][1:] = list(tmp[0])
                elif phrase[1][1] == "$":
                    for i in range(4, 2, -1):
                        tmp = self.logic.find_hidden_polygons(i)
                        if len(tmp) > 0:
                            phrase[1][1:] = list(tmp[0])
                            break
            if len(phrase[1]) == 5:
                self.parseQuad(phrase[1])
            return ['Area', *phrase[1][1:]]

        if phrase[0] == "RatioOf" and len(phrase) == 2:
            return self.findTarget(['Find', phrase[1]])

        if phrase[0] in ["SinOf", "CosOf", "TanOf", "CotOf", "HalfOf", "SquareOf", "SqrtOf"]:
            if phrase[1][0] == "Angle":
                # In this case, 'MeasureOf' may be skipped.
                phrase[1] = ['MeasureOf', phrase[1]]
            return [phrase[0], self.findTarget(['Find', phrase[1]])]
        
        if phrase[0] in ["RatioOf", "Add", "Mul", "SumOf"]:
            return [phrase[0]] + [self.findTarget(['Find', x]) for x in phrase[1:]]

        return None
    
        