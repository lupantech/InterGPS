import numpy as np
from geosolver.ontology.instantiator_definitions import instantiators

__author__ = 'minjoon'

def distance_between_points(p0, p1):
    return np.linalg.norm(dimension_wise_distance_between_points(p0, p1))


def distance_between_points_squared(p0, p1):
    return (p0.x-p1.x)**2 + (p0.y-p1.y)**2


def dimension_wise_distance_between_points(p0, p1):
    return abs(p0.x-p1.x), abs(p0.y-p1.y)


def dot_distance_between_points(unit_vector, point, reference_point):
    """
    Distance between two points dot-producted by the unit vector

    :param line:
    :param point:
    :param reference_point:
    :return:
    """
    return np.dot(unit_vector, np.array(point) - np.array(reference_point))


def line_length(line):
    return distance_between_points(line.a, line.b)


def line_vector(line):
    array = (np.array(line[1]) - np.array(line[0]))
    return array


def line_unit_vector(line):
    array = line_vector(line)/line_length(line)
    return tuple(array)


def line_normal_vector(line):
    unit_vector = line_unit_vector(line)
    return unit_vector[1], -unit_vector[0]


def circumference(circle):
    return 2*np.pi*circle.radius


def midpoint(p0, p1):
    return instantiators['point'](*((np.array(p0) + np.array(p1))/2.0))


def distance_between_line_and_point(line, point):
    """
    This function is slow... Please improve!

    :param line:
    :param point:
    :return:
    """
    p = midpoint(line.a, line.b)
    vector = point.x - p.x, point.y - p.y
    u = line_unit_vector(line)
    n = line_normal_vector(line)
    perpendicular_distance = abs(np.dot(vector, n))
    parallel_distance = abs(np.dot(vector, u))
    if parallel_distance <= line_length(line)/2.0:
        return perpendicular_distance
    else:
        return min(distance_between_points(point, line.a),
                   distance_between_points(point, line.b))

def perpendicular_distance_between_line_and_point(line, point):
    p = midpoint(line.a, line.b)
    vector = point.x - p.x, point.y - p.y
    u = line_unit_vector(line)
    n = line_normal_vector(line)
    perpendicular_distance = abs(np.dot(vector, n))
    return perpendicular_distance

def distance_between_circle_and_point(circle, point):
    return abs(circle.radius - distance_between_points(circle.center, point))


def distance_between_arc_and_point(arc, point):
    angle_a = cartesian_angle(arc.circle.center, arc.a)
    angle_b = cartesian_angle(arc.circle.center, arc.b)
    angle_p = cartesian_angle(arc.circle.center, point)
    db = signed_distance_between_cartesian_angles(angle_a, angle_b)
    dp = signed_distance_between_cartesian_angles(angle_a, angle_p)
    if dp <= db:
        return distance_between_circle_and_point(arc.circle, point)
    else:
        return min(distance_between_points(arc.a, point), distance_between_points(arc.b, point))


def arc_length(arc):
    angle_a = cartesian_angle(arc.circle.center, arc.a)
    angle_b = cartesian_angle(arc.circle.center, arc.b)
    angle = signed_distance_between_cartesian_angles(angle_a, angle_b)
    return angle*arc.circle.radius


def intersections_between_lines(line0, line1, eps):
    line0a = np.array(line0)
    line1a = np.array(line1)
    x = line0a[0] - line1a[0]
    d1 = line1a[1] - line1a[0]
    d2 = line0a[1] - line0a[0]
    cross = d1[0]*d2[1] - d1[1]*d2[0]
    if abs(cross) < eps:
        return []

    t1 = float(x[0]*d2[1] - x[1]*d2[0])/cross
    r = line1a[0] + d1*t1
    p = instantiators['point'](*r)
    if distance_between_line_and_point(line1, p) < eps and distance_between_line_and_point(line0, p) < eps:
        return [p]
    else:
        return []


def intersections_between_circle_and_line(circle, line, eps):
    min_angle = 40
    temp_sln = []
    normal_vector = np.array(line_normal_vector(line))
    parallel_vector = np.array(line_unit_vector(line))
    d = np.dot(np.array(midpoint(*line))-np.array(circle.center), normal_vector)
    perp_vector = d*normal_vector

    # Tangency
    D = circle.radius**2 - d**2

    # Error tolerant step
    if D < 0:
        D = (circle.radius + eps)**2 - d**2
        if D >= 0:
            par_vector = np.sqrt(D) * parallel_vector
            pt = instantiators['point'](*(circle.center + perp_vector))
            temp_sln.append(pt)

    else:
        par_vector = np.sqrt(D) * parallel_vector
        pt = instantiators['point'](*(np.array(circle.center) + perp_vector + par_vector))
        temp_sln.append(pt)
        pt = instantiators['point'](*(np.array(circle.center) + perp_vector - par_vector))
        temp_sln.append(pt)

    # Check if the point is on the line
    sln = []
    for point in temp_sln:
        if distance_between_line_and_point(line, point) < eps:
            pt = instantiators['point'](*point)
            sln.append(pt)

    if len(sln) == 2:
        angle = instantiators['angle'](sln[0], circle.center, sln[1])
        if angle_in_degree(angle, True) < min_angle:
            return [midpoint(sln[0], sln[1])]

    return sln

def intersections_between_circles(circle0, circle1):
    """
    TO BE IMPLEMENTED
    :param circle0:
    :param circle1:
    :return:
    """
    return []


def angle_in_radian(angle, smaller=False):
    """
    a = line_length(instantiators['line'](angle.b, angle.c))
    b = line_length(instantiators['line'](angle.c, angle.a))
    c = line_length(instantiators['line'](angle.a, angle.b))
    value = (c**2 + a**2 - b**2) / (2*c*a)
    smaller_angle = np.arccos(value)
    if smaller:
        return smaller_angle
    else:
        a0 = cartesian_angle(angle.b, angle.a)
        a1 = cartesian_angle(angle.b, angle.c)
        return signed_distance_between_cartesian_angles(a0, a1)
    """
    a0 = cartesian_angle(angle.b, angle.a)
    a1 = cartesian_angle(angle.b, angle.c)
    diff = signed_distance_between_cartesian_angles(a0, a1)
    if smaller and diff > np.pi:
        return 2*np.pi - diff
    return diff

def angle_in_degree(angle, smaller=True):
    return 180*angle_in_radian(angle, smaller=smaller)/np.pi


def cartesian_angle(center, point):
    vector = point.x-center.x, point.y-center.y
    angle = np.arctan2(vector[1], vector[0])
    if angle < 0:
        angle += 2*np.pi
    return angle


def signed_distance_between_cartesian_angles(a0, a1):
    distance = a1 - a0
    if distance < 0:
        distance += 2*np.pi
    return distance


def arc_midpoint(arc):
    circle = arc.circle
    radius = circle.radius
    caa = cartesian_angle(circle.center, arc.a)
    cab = cartesian_angle(circle.center, arc.b)
    cam = caa + signed_distance_between_cartesian_angles(caa, cab)/2.0
    mp = instantiators['point'](radius*np.cos(cam), radius*np.sin(cam))
    return mp


def normalize_angle(angle):
    if angle < 0:
        return angle+np.ceil(-angle/(2*np.pi))*2*np.pi
    elif angle > 2*np.pi:
        return angle-(np.ceil(angle/(2*np.pi))-1)*2*np.pi
    return angle


def horizontal_angle(angle):
    angle = normalize_angle(angle)
    if angle > np.pi:
        return min(angle-np.pi, 2*np.pi-angle)
    else:
        return min(angle, np.pi-angle)

def polygon_is_convex(points):
    angles = [instantiators['angle'](points[index-2], points[index-1], point) for index, point in enumerate(points)]
    calc = sum(angle_in_radian(angle, False) for angle in angles)
    ans = np.pi*(len(points)-2)
    if calc > ans + 10:
        return False
    return True

def area_of_polygon(points):
    area = 0.5*abs(sum(points[index-1][0]*p[1]-p[0]*points[index-1][1] for index, p in enumerate(points)))
    return area

