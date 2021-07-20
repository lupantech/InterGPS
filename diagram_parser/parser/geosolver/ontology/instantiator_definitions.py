"""
Semantic definitions of ontology.

All functions need to be defined in terms of sympy's symbolic representations.
See ontology/basic_definitions.py for ontology.
If the function needs to return a truth value, then it must return an instance of 'Truth'.
Otherwise, it returns a sympy expression (can be a constant).
"""
from collections import namedtuple

__author__ = 'minjoon'


instantiator_defs = {
    'point': (('x', 'number'), ('y', 'number')),
    'line': (('a', 'point'), ('b', 'point')),
    'angle': (('a', 'point'), ('b', 'point'), ('c', 'point')),
    'circle': (('center', 'point'), ('radius', 'number')),
    'arc': (('circle', 'circle'), ('a', 'point'), ('b', 'point')),
    'triangle': (('a', 'point'), ('b', 'point'), ('c', 'point')),
    'quad': (('a', 'point'), ('b', 'point'), ('c', 'point'), ('d', 'point')),
    'hexagon': (('a', 'point'), ('b', 'point'), ('c', 'point'), ('d', 'point'), ('e', 'point'), ('f', 'point')),
    'para': (('a', 'point'), ('b', 'point'), ('c', 'point'), ('d', 'point')),
    'rectangle': (('a', 'point'), ('b', 'point'), ('c', 'point'), ('d', 'point')),
    'trapezoid': (('a', 'point'), ('b', 'point'), ('c', 'point'), ('d', 'point')),
    'rhombus': (('a', 'point'), ('b', 'point'), ('c', 'point'), ('d', 'point')),
    'square': (('a', 'point'), ('b', 'point'), ('c', 'point'), ('d', 'point')),
}

class polygon(tuple):
    def __new__(self, *points):
        return tuple.__new__(polygon, points)



"""
Initialize instantiators based on type_defs
"""
instantiators = {}
instantiators['polygon'] = polygon
for key, value in instantiator_defs.items():
    args, _ = zip(*value)
    nt = namedtuple(key, ' '.join(args))
    instantiators[key] = nt


def get_polygon(*args):
    if len(args) == 3:
        return instantiators['triangle'](*args)
    elif len(args) == 4:
        return instantiators['quadrilateral'](*args)
    else:
        raise Exception()

# instantiators['get_polygon'] = get_polygon
