from sklearn.cluster import KMeans

import itertools
from geosolver.diagram.states import PrimitiveParse, CoreParse
from geosolver.ontology.instantiator_definitions import instantiators
from geosolver.diagram.computational_geometry import intersections_between_lines, intersections_between_circle_and_line, \
    intersections_between_circles, distance_between_points
import geosolver.parameters as params
from geosolver.ontology.ontology_definitions import VariableSignature, FormulaNode

__author__ = 'minjoon'


def parse_core(primitive_parse):
    all_intersections = _get_all_intersections(primitive_parse, params.INTERSECTION_EPS)
    clustered_intersections = _cluster_intersections(all_intersections, params.KMEANS_RADIUS_THRESHOLD)
    intersections = dict(enumerate(clustered_intersections))
    assignment = {}
    point_variables = {}
    for idx in intersections.keys():
        id_ = "point_%d" % idx
        vs = VariableSignature(id_, 'point')
        point_variables[idx] = FormulaNode(vs, [])
        assignment[id_] = intersections[idx]
    circles = _get_circles(primitive_parse, intersections)
    radius_variables = {}
    for point_idx, d in circles.items():
        radius_variables[point_idx] = {}
        for radius_idx in d.keys():
            id_ = "radius_%d_%d" % (point_idx, radius_idx)
            vs = VariableSignature(id_, 'number')
            radius_variables[point_idx][radius_idx] = FormulaNode(vs, [])
            assignment[id_] = circles[point_idx][radius_idx].radius
    core_parse = CoreParse(primitive_parse, intersections, point_variables, circles, radius_variables, assignment)
    return core_parse


def _get_all_intersections(primitive_parse, eps):
    assert isinstance(primitive_parse, PrimitiveParse)

    intersections = []
    for pr0, pr1 in itertools.combinations(primitive_parse.primitives.values(), 2):
        intersections.extend(_get_intersections_between_primitives(pr0, pr1, eps))

    for line in primitive_parse.lines.values():
        intersections.extend(line)

    for circle in primitive_parse.circles.values():
        intersections.append(circle.center)

    return intersections


def _cluster_intersections(intersections, radius_threshold):
    """
    Increase number of clusters until all clusters' radius < radius_threshold
    Stop right away

    :param intersections:
    :param sigma_threshold:
    :return:
    """
    if len(intersections) == 0:
        return []
    n = 1
    while True:
        km = KMeans(n)
        assignments = km.fit_predict(intersections)
        centers = [instantiators['point'](*p) for p in km.cluster_centers_]
        radii = []
        for center_idx, center in enumerate(centers):
            curr_points = [p for idx, p in enumerate(intersections) if assignments[idx] == center_idx]
            radius = _get_radius(center, curr_points)
            radii.append(radius)
        if max(radii) <= radius_threshold:
            return centers
        else:
            n += 1

def _get_radius(center, points):
    return max(distance_between_points(center, point) for point in points)


def _get_intersections_between_primitives(obj0, obj1, eps):
    """
    Intersections between two primitives
    :param obj0:
    :param obj1:
    :return:
    """
    is_line0 = isinstance(obj0, instantiators['line'])
    is_circle0 = isinstance(obj0, instantiators['circle'])
    is_line1 = isinstance(obj1, instantiators['line'])
    is_circle1 = isinstance(obj1, instantiators['circle'])
    if is_line0 and is_line1:
        return intersections_between_lines(obj0, obj1, eps)
    elif is_line0 and is_circle1:
        return intersections_between_circle_and_line(obj1, obj0, eps)
    elif is_circle0 and is_line1:
        return intersections_between_circle_and_line(obj0, obj1, eps)
    elif is_circle0 and is_circle1:
        return intersections_between_circles(obj0, obj1)
    else:
        raise Exception()


def _get_circles(primitive_parse, intersection_points):
    """
    A dictionary of dictionaries, where key of the top dictionary is center point.
    The bottom dictionary contains radii (if multiple circles exist with the same center).

    :param core_parse:
    :return:
    """
    eps = params.CIRCLE_EPS
    circle_dict = {}
    for point_key, point in intersection_points.items():
        d = {}
        radius_key = 0
        for circle in primitive_parse.circles.values():
            if distance_between_points(point, circle.center) <= eps:
                d[radius_key] = circle
                radius_key += 1
        if len(d) > 0:
            circle_dict[point_key] = d
    return circle_dict
