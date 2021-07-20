import logging

import numpy as np

from geosolver.diagram.states import PrimitiveParse
from geosolver.diagram.computational_geometry import line_length, circumference, \
    distance_between_circle_and_point, midpoint, line_unit_vector, line_normal_vector, \
    distance_between_points_squared, distance_between_line_and_point
from geosolver.ontology.instantiator_definitions import instantiators
import geosolver.parameters as params


__author__ = 'minjoon'


def select_primitives(primitive_parse):
    assert isinstance(primitive_parse, PrimitiveParse)
    if len(primitive_parse.primitives) == 0:
        logging.error("No primitive detected.")
        return primitive_parse
    pixels_dict = _get_pixels_dict(primitive_parse,
                                   params.LINE_EPS, params.CIRCLE_EPS)
    selected_primitives = {}
    remaining_primitives = primitive_parse.primitives.copy()
    reward = 0
    while len(remaining_primitives) > 0:
        key = _get_next_primitive_key(selected_primitives, remaining_primitives, pixels_dict)
        updated_selected_primitives = selected_primitives.copy()
        updated_selected_primitives[key] = remaining_primitives[key]
        new_reward = _evaluate_reward(updated_selected_primitives, pixels_dict)
        if new_reward - reward > params.PRIMITIVE_SELECTION_MIN_GAIN:
            selected_primitives = updated_selected_primitives
            del remaining_primitives[key]
            reward = new_reward
        else:
            break

    new_primitive_parse = _get_primitive_parse(primitive_parse.image_segment_parse, selected_primitives)
    return new_primitive_parse

def _get_primitive_parse(segment_parse, primitives):
    lines = dict(pair for pair in primitives.items()
                 if isinstance(pair[1], instantiators['line']))
    circles = dict(pair for pair in primitives.items()
                   if isinstance(pair[1], instantiators['circle']))
    return PrimitiveParse(segment_parse, lines, circles)

# jabbyjiang add
def merge_dict(a, b):
    # print (b)
    # print (type(b))
    # print (type(a))
    d = a.copy()
    d[b[0]] = b[1]
    return d

def _get_next_primitive_key(selected_primitives, remaining_primitives, pixels_dict):
    return max(remaining_primitives.items(),
               # key=lambda p: _evaluate_reward(dict(selected_primitives.items()+[p]), pixels_dict))[0]
               key=lambda p: _evaluate_reward(merge_dict(selected_primitives, p), pixels_dict))[0]


def _get_pixels_dict(primitive_parse, line_eps, circle_eps):
    primitives = primitive_parse.primitives
    pixels = primitive_parse.image_segment_parse.diagram_image_segment.pixels
    pixels_dict = {'all': pixels}
    for key, primitive in primitives.items():
        if isinstance(primitive, instantiators['line']):
            eps = line_eps
            curr_pixels = _get_pixels_near_line(pixels, primitive, eps)
            pixels_dict[key] = curr_pixels

            """
            image = cv2.cvtColor(primitive_parse.image_segment_parse.diagram_image_segment.segmented_image, cv2.COLOR_GRAY2BGR)
            draw_line(image, primitive)
            display_image(image)
            for pixel in curr_pixels:
                draw_point(image, pixel)
            display_image(image)
            """

            a_pixels = _get_pixels_near_point(pixels, primitive.a, eps)
            b_pixels = _get_pixels_near_point(pixels, primitive.b, eps)
            pixels_dict[primitive.a] = a_pixels
            pixels_dict[primitive.b] = b_pixels

        elif isinstance(primitive, instantiators['circle']):
            eps = circle_eps
            curr_pixels = set(pixel for pixel in pixels if distance_between_circle_and_point(primitive, pixel) < eps)
            pixels_dict[key] = curr_pixels
    return pixels_dict


def _get_pixels_near_point(pixels, point, eps):
    return set(pixel for pixel in pixels if distance_between_points_squared(pixel, point) <= eps**2)


def _evaluate_reward(partial_primitives, pixels_dict):
    x = [_coverage(partial_primitives, pixels_dict),
         _pixel_num(partial_primitives, pixels_dict),
         _length_sum(partial_primitives),
         _coherence(partial_primitives),
         _end_pixel_num(partial_primitives, pixels_dict),
         ]
    w = [1, -0.1, -0.7, 00, 0.1]
    return np.dot(x, w)


def _coverage(partial_primitives, pixels_dict):
    if len(partial_primitives) == 0:
        return 0
    coverage = len(set.union(*[pixels_dict[key] for key in partial_primitives]))
    return coverage


def _pixel_num(partial_primitives, pixels_dict):
    if len(partial_primitives) == 0:
        return 0
    num = sum(len(pixels_dict[key]) for key in partial_primitives)
    return num

def _end_pixel_num(partial_primitives, pixels_dict):
    lines = _get_lines(partial_primitives)
    if len(lines) == 0:
        return 0
    coverage = set.union(*[pixels_dict[primitive.a] for primitive in lines])
    coverage2 = set.union(*[pixels_dict[primitive.b] for primitive in lines])
    return len(set.union(coverage, coverage2))



def _get_pixels_near_line(pixels, line, eps):
    """
    This can be replaced with shorter, more inefficient code.
    Written to boost up the speed.
    :param pixels:
    :param line:
    :param eps:
    :return:
    """
    #return set(pixel for pixel in pixels if distance_between_line_and_point(line, pixel) <= eps)

    p = midpoint(line.a, line.b)
    u = line_unit_vector(line)
    n = line_normal_vector(line)
    half_length = line_length(line)/2.0
    eps_squared = eps**2

    near_pixels = set()
    for point in pixels:
        vector = point.x - p.x, point.y - p.y
        perpendicular_distance = abs(np.dot(vector, n))
        if perpendicular_distance > eps:
            continue
        parallel_distance = abs(np.dot(vector, u))
        if parallel_distance <= half_length:
            near_pixels.add(point)
        else:
            if distance_between_points_squared(point, line.a) <= eps_squared or \
                    distance_between_points_squared(point, line.b) <= eps_squared:
                near_pixels.add(point)
    return near_pixels


def _length_sum(partial_primitives):
    """
    Computes the sum of squareroot of sum of lengths.
    This way, longer lines / bigger circles are preferred.

    :param partial_primitives:
    :return:
    """
    if len(partial_primitives) == 0:
        return 0
    total = 0
    for primitive in partial_primitives.values():
        if isinstance(primitive, instantiators['circle']):
            total += circumference(primitive)
        elif isinstance(primitive, instantiators['line']):
            pass
        else:
            raise Exception()
    return total


def _coherence(partial_primitives):
    scores = []
    for idx, primitive in partial_primitives.items():
        if isinstance(primitive, instantiators['line']):
            score = _line_coherence(partial_primitives, idx)
        elif isinstance(primitive, instantiators['circle']):
            score = _circle_coherence(partial_primitives, idx)
        scores.append(score)
    return np.mean(scores)


def _line_coherence(partial_primitives, curr_idx):
    if len(partial_primitives) == 0:
        return 0
    line = partial_primitives[curr_idx]
    distances0 = [_distance_from_point(line.a, primitive) for primitive in partial_primitives.values()]
    distances1 = [_distance_from_point(line.b, primitive) for primitive in partial_primitives.values()]
    return _distance_score(np.mean([min(distances0), min(distances1)]))


def _circle_coherence(partial_primitives, curr_idx):
    if len(partial_primitives) == 0:
        return 0
    circle = partial_primitives[curr_idx]
    distances = [_distance_from_point(circle.center, primitive) for primitive in partial_primitives.values()]
    return _distance_score(min(distances))


def _distance_from_point(point, primitive):
    if isinstance(primitive, instantiators['line']):
        return distance_between_line_and_point(primitive, point)
    elif isinstance(primitive, instantiators['circle']):
        return distance_between_circle_and_point(primitive, point)


def _distance_score(distance):
    eps = 10
    if distance < eps:
        return float(eps-distance)/eps
    else:
        return 0


def _get_lines(partial_primitives):
    return [p for p in partial_primitives.values() if isinstance(p, instantiators['line'])]