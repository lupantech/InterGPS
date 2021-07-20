import cv2
import numpy as np

from geosolver.diagram.states import ImageSegmentParse, PrimitiveParse
from geosolver.diagram.computational_geometry import dot_distance_between_points
from geosolver.ontology.instantiator_definitions import instantiators
from geosolver.parameters import hough_line_parameters as line_params
from geosolver.parameters import hough_circle_parameters as circle_params
from geosolver.utils.num import dimension_wise_non_maximum_suppression

__author__ = 'minjoon'

def parse_primitives(image_segment_parse):
    assert isinstance(image_segment_parse, ImageSegmentParse)
    diagram_segment = image_segment_parse.diagram_image_segment
    lines = _get_lines(diagram_segment, line_params)
    circles = _get_circles(diagram_segment, circle_params)
    line_dict = {idx: line for idx, line in enumerate(lines)}
    circle_dict = {idx+len(lines): circle for idx, circle in enumerate(circles)}
    primitive_parse = PrimitiveParse(image_segment_parse, line_dict, circle_dict)
    return primitive_parse


def _get_lines(image_segment, params):
    lines = []
    temp = cv2.HoughLines(image_segment.binarized_segmented_image, params.rho, params.theta, params.threshold)
    if temp is None:
        return lines

    rho_theta_pairs = [temp[idx][0] for idx in range(len(temp))]
    if len(rho_theta_pairs) > params.max_num:
        rho_theta_pairs = rho_theta_pairs[:params.max_num]


    nms_rho_theta_pairs = dimension_wise_non_maximum_suppression(rho_theta_pairs, (params.nms_rho, params.nms_theta),
                                                                 _dimension_wise_distances_between_rho_theta_pairs)

    for rho_theta_pair in rho_theta_pairs:
        curr_lines = _segment_line(image_segment, rho_theta_pair, params)
        lines.extend(curr_lines)

    return lines


def _get_circles(image_segment, params):

    temp = cv2.HoughCircles(image_segment.segmented_image, cv2.HOUGH_GRADIENT, params.dp, params.minDist,
                            param1=params.param1, param2=params.param2,
                            minRadius=params.minRadius, maxRadius=params.maxRadius)
    if temp is None:
        return []

    circle_tuples = temp[0]
    if len(circle_tuples) > params.max_num:
        circle_tuples = circle_tuples[:params.max_num]

    circles = [instantiators['circle'](instantiators['point'](x, y), radius)
               for x, y, radius in circle_tuples]
    return circles


def _segment_line(image_segment, rho_theta_pair, params):
    lines = []
    near_pixels = _get_pixels_near_rho_theta_pair(image_segment.pixels, rho_theta_pair, params.eps)
    if len(near_pixels) == 0:
        return lines

    reference_pixel = near_pixels[0]
    distances = [dot_distance_between_points(_rho_theta_pair_unit_vector(rho_theta_pair), p, reference_pixel)
                 for p in near_pixels]
    order = np.argsort(distances)
    start_idx = None
    end_idx = None

    for order_idx, idx in enumerate(order):
        if start_idx is None:
            start_idx = idx
            end_idx = idx
        else:
            d0 = distances[idx]
            d1 = distances[order[order_idx-1]]
            if abs(d0-d1) > params.max_gap or order_idx == len(order) - 1:
                length = abs(distances[start_idx] - distances[end_idx])
                if length > params.min_length:
                    p0 = near_pixels[start_idx]
                    p1 = near_pixels[end_idx]
                    line = instantiators['line'](p0, p1)
                    lines.append(line)
                start_idx = None
            else:
                end_idx = idx

    return lines


def _get_pixels_near_rho_theta_pair(pixels, rho_theta_pair, eps):
    near_pixels = [pixel for pixel in pixels
                   if _distance_between_rho_theta_pair_and_point(rho_theta_pair, pixel) <= eps]
    return near_pixels


def _distance_between_rho_theta_pair_and_point(rho_theta_pair, point):
    rho, theta = rho_theta_pair
    x, y = point
    return abs(rho - x*np.cos(theta) - y*np.sin(theta))


def _rho_theta_pair_unit_vector(rho_theta_pair):
    _, theta = rho_theta_pair
    return tuple([np.sin(theta), -np.cos(theta)])


def _dimension_wise_distances_between_rho_theta_pairs(pair0, pair1):
    rho0, theta0 = pair0
    rho1, theta1 = pair1
    rho_distance = abs(rho0 - rho1)
    theta_distance = min(abs(theta0-theta1),
                         abs(theta0-theta1+2*np.pi),
                         abs(theta0-theta1-2*np.pi))
    return rho_distance, theta_distance