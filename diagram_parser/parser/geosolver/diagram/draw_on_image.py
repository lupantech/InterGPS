import cv2
import numpy as np

from geosolver.diagram.computational_geometry import cartesian_angle, line_length
from geosolver.ontology.instantiator_definitions import instantiators
from geosolver.utils.num import round_vector

__author__ = 'minjoon'


def draw_instance(image, instance, **kwargs):
    for key, instantiator in instantiators.items():
        if isinstance(instance, instantiator):
            if key in ['triangle', 'quad']:
                draw_polygon(image, instance, **kwargs)
            else:
                eval("draw_%s(image, instance, **kwargs)" % key)


def draw_line(image, line, offset=(0, 0), color=(0, 0, 255), thickness=1):
    pt1 = round_vector(np.array(line.a) + offset)
    pt2 = round_vector(np.array(line.b) + offset)
    cv2.line(image, pt1, pt2, color, thickness=thickness)


def draw_circle(image, circle, offset=(0, 0), color=(0, 0, 255), thickness=1):
    center = round_vector(np.array(circle.center) + offset)
    cv2.circle(image, center, circle.radius, color, thickness=thickness)


def draw_point(image, point, offset=(0, 0), color=(255, 0, 0), thickness=2, radius=2):
    circle = instantiators['circle'](point, radius)
    draw_circle(image, circle, offset=offset, color=color, thickness=thickness)


def draw_arc(image, arc, offset=(0, 0), color=(0, 0, 255), thickness=1):
    caa = cartesian_angle(arc.circle.center, arc.a) * 180/np.pi
    cab = cartesian_angle(arc.circle.center, arc.b) * 180/np.pi
    if caa > cab:
        caa -= 360
    center = tuple(round_vector(np.array(arc.circle.center) + offset))
    radius = int(round(arc.circle.radius))
    cv2.ellipse(image, center, (radius, radius), 0, caa, cab, color, thickness)


def draw_angle(image, angle, offset=(0, 0), color=(0, 0, 255), thickness=1, color2=(255, 0, 0), thickness2=1):
    line0 = instantiators['line'](angle.b, angle.a)
    line1 = instantiators['line'](angle.b, angle.c)
    draw_line(image, line0, offset=offset, color=color, thickness=thickness)
    draw_line(image, line1, offset=offset, color=color, thickness=thickness)
    radius = 0.3 * min(line_length(line0), line_length(line1))
    circle = instantiators['circle'](angle.b, radius)
    # FIXME : this arc definition is broken. Okay for now, but needs to fix.
    arc = instantiators['arc'](circle, angle.a, angle.c)
    draw_arc(image, arc, offset=offset, color=color2, thickness=thickness2)


def draw_polygon(image, instance, offset=(0, 0), color=(0, 0, 255), thickness=1):
    lines = [instantiators['line'](instance[idx-1], arg) for idx, arg in enumerate(instance)]
    for line in lines:
        draw_line(image, line, offset=offset, color=color, thickness=thickness)


def draw_label(image, label, offset=(0, 0), fontScale=2, color=(0, 0, 0), thickness=1):
    position = round_vector(np.array(label.position) + offset)
    cv2.putText(image, label.text, position, cv2.FONT_HERSHEY_PLAIN, fontScale, color, thickness=thickness)
