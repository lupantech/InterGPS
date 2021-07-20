from geosolver.solver.numeric_solver import NumericSolver
from geosolver.solver.variable_handler import VariableHandler
import numpy as np

__author__ = 'minjoon'

def example_0():
    """
    AB = x, BC = 3, CA = 4. Is an answer x=5, x=8 possible?
    :return:
    """
    vh = VariableHandler()
    x = vh.number('x')
    A = vh.point('A')
    B = vh.point('B')
    C = vh.point('C')
    AB = vh.line(A, B)
    BC = vh.line(B, C)
    CA = vh.line(C, A)
    c = vh.apply('LengthOf', AB)
    a = vh.apply('LengthOf', BC)
    b = vh.apply('LengthOf', CA)
    p1 = a == 3
    p2 = b == 4
    p3 = c == x
    q1 = x == 8
    q2 = x == 5
    ns = NumericSolver([p1, p2, p3], vh)
    print(ns.find_assignment(q1))
    print(ns.find_assignment(q2))

def example_1():
    """
    AB perpendicular to BC, AB = x, and BC = 4. Is CA = sqrt(x^2+16) a correct answer?
    :return:
    """
    vh = VariableHandler()
    x = vh.number('x')
    A = vh.point('A')
    B = vh.point('B')
    C = vh.point('C')
    AB = vh.line(A, B)
    BC = vh.line(B, C)
    CA = vh.line(C, A)
    c = vh.apply('LengthOf', AB)
    a = vh.apply('LengthOf', BC)
    b = vh.apply('LengthOf', CA)
    p1 = a == 4
    p2 = c == x
    p3 = vh.apply('Perpendicular', AB, BC)
    q1 = b == (16 + x**2)**0.5
    q2 = b == x**2

    ns = NumericSolver([p1, p2, p3], vh)
    print(ns.find_assignment(q1))  # find_assignment simply analyzes whether the query relation can be satisfied
    print(ns.query_invar(q1))  # query_invar analyzes whether the query relation must hold true
    print(ns.find_assignment(q2))  # this is satisfiable; there exists x that satisfies q2.
    print(ns.query_invar(q2))  # this is False because q2 is not true for all possible x.

def example_2():
    """
    AB is tangent to circle O, AO = BO = 1 and AB = sqrt(2). What is the radius of circle O?
    :return:
    """
    vh = VariableHandler()
    O = vh.point('O')
    A = vh.point('A')
    B = vh.point('B')
    AO = vh.line(A, O)
    BO = vh.line(B, O)
    AB = vh.line(A, B)
    # vh.circle() with one argument assumes the radius is an unknown value (i.e. variable).
    # if you want to define radius, just give it two arguments, e.g. vh.circle(O, r)
    cO = vh.circle(O)
    a = vh.apply('LengthOf', AO)
    b = vh.apply('LengthOf', BO)
    o = vh.apply('LengthOf', AB)
    p1 = a == 1
    p2 = b == 1
    p3 = o == np.sqrt(2)
    p4 = vh.apply('Tangent', AB, cO)
    ns = NumericSolver([p1, p2, p3, p4], vh)
    ans = vh.apply('RadiusOf', cO)
    if ns.is_sat():
        print ns.evaluate(ans), 1/np.sqrt(2)  # the latter is the true answer
    else:
        print("Given information is not satisfiable.")


def example_3():
    """
    Question ID: 1
    In the diagram at the right, circle O has a radius of 5, and CE = 2.
    Diameter AC is perpendicular to chord BD at E.
    What is the length of BD?
    :return:
    """
    vh = VariableHandler()
    A = vh.point('A')
    B = vh.point('B')
    C = vh.point('C')
    D = vh.point('D')
    E = vh.point('E')
    O = vh.point('O')
    CE = vh.line(C, E)
    AC = vh.line(A, C)
    BD = vh.line(B, D)
    cO = vh.circle(O)
    p1 = vh.apply('RadiusOf', cO) == 5  # Equals(RadiusOf(cO), 5))
    p2 = vh.apply('LengthOf', CE) == 2  # Equals(LengthOf(CE), 2)
    p3 = vh.apply('IsDiameterLineOf', AC, cO)
    p4 = vh.apply('IsChordOf', BD, cO)
    p5 = vh.apply('Perpendicular', AC, BD)
    p6 = vh.apply('PointLiesOnLine', E, AC)  # AC intersects BD at E is broken down into two atoms
    p7 = vh.apply('PointLiesOnLine', E, BD)
    ps = [p1, p2, p3, p4, p5, p6, p7]
    ns = NumericSolver(ps, vh)
    ans = vh.apply('LengthOf', BD)
    if ns.is_sat():
        print ns.evaluate(ans), 8  # 8 is the answer
    else:
        print "Given information is not satisfiable."

def test_pyipopt():
    pass


if __name__ == "__main__":
    example_3()
