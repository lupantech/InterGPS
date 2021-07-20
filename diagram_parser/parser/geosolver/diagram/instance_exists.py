"""
"instance" referring to any instance instantiated by instantiators.
Ex. point, line, circle, arc, triangle, quadrilateral
Exists returns True / False

"""
import numpy as np

from geosolver.diagram.computational_geometry import line_length, line_unit_vector, distance_between_points, \
    distance_between_line_and_point, distance_between_arc_and_point, arc_length, distance_between_circle_and_point, \
    circumference
from geosolver.diagram.states import CoreParse
from geosolver.ontology.instantiator_definitions import instantiators
from geosolver.parameters import LINE_EPS

__author__ = 'minjoon'


def instance_exists(diagram_parse, instance):
    if isinstance(instance, instantiators['line']):
        return _line_exists(diagram_parse, instance)
    elif isinstance(instance, instantiators['arc']):
        return _arc_exists(diagram_parse, instance)


def _line_exists(diagram_parse, line):
    # TODO : smarter line_exists function needed (check continuity, etc.)
    eps = LINE_EPS
    multiplier = 1.0
    assert isinstance(diagram_parse, CoreParse)
    pixels = diagram_parse.primitive_parse.image_segment_parse.diagram_image_segment.pixels
    near_pixels = set(pixel for pixel in pixels if distance_between_line_and_point(line, pixel) <= eps)
    length = line_length(line)
    ratio = float(len(near_pixels))/length
    if ratio < multiplier:
        return False
    return True


def _arc_exists(diagram_parse, arc):
    eps = 4
    multiplier = 1
    assert isinstance(diagram_parse, CoreParse)
    pixels = diagram_parse.primitive_parse.image_segment_parse.diagram_image_segment.pixels
    near_pixels = set(pixel for pixel in pixels if distance_between_arc_and_point(arc, pixel) <= eps)
    length = arc_length(arc)
    ratio = float(len(near_pixels))/length
    if ratio < multiplier:
        return False
    return True


def _circle_exists(diagram_parse, circle):
    eps = 4
    multiplier = 2
    assert isinstance(diagram_parse, CoreParse)
    pixels = diagram_parse.primitive_parse.image_segment_parse.diagram_image_segment.pixels
    near_pixels = set(pixel for pixel in pixels if distance_between_circle_and_point(circle, pixel) <= eps)
    length = circumference(circle)
    if len(near_pixels) < multiplier*length:
        return False
    return True

def _distance_to_closest_point(point, points):
    return min(distance_between_points(point, p) for p in points)
