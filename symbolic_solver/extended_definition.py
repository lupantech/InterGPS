from basic_definition import BasicDefinition
from utils import isNumber

from kanren import facts
from kanren import run, var

from sympy import Symbol

from itertools import permutations, product, combinations

import math


class ExtendedDefinition(BasicDefinition):
    def __init__(self, debug):
        super(ExtendedDefinition, self).__init__(debug)
        # self.symbols = [] 

    def parseAngle(self, angle):
        if len(angle) == 3:
            # The normal case
            return angle
        elif len(angle) == 1:
            # Maybe the angle will be given in only one letter.
            # Then we should add two more points to create a standard angle.
            angle = angle[0]
            points = self.find_all_lines_for_point(angle)
            assert len(points) >= 2, "Change %s to angle failed." % angle
            for center in self.find_all_circles():
                if len(points) > 2 and center in points:
                    points.remove(center)
            x = points[0]
            line = self.find_all_points_on_line((x, angle))
            valid_y = [y for y in points[1:] if y not in line]
            assert len(valid_y) > 0, "Change %s to angle failed." % angle
            return [x, angle, valid_y[0]]
        return None

    def parseLine(self, line, extra_point=None):
        if type(line) in [list, tuple] and len(line) == 1:
            line = line[0]

        if type(line) in [list, tuple]:
            assert len(line) == 2, "The length of line elements must be 2."
            return line

        if line == '$':
            # Solve with Line($)
            if extra_point is not None:
                line = self.find_all_lines_for_point(extra_point)  # find all linked points
                if len(line) == 2:
                    return line
            return None

        # Sometimes we will use a lowercase letter to represent a line.
        # e.g. Parallel(m, n)
        if line.islower():
            line_value = Symbol(line)  # convert a char to a symbolic variable
            line = self.check_line_with_length(line_value)
            if len(line) > 0:
                return line[0]
        return None

    def parseArc(self, arc):
        """
        In the given logic forms, we use two/three points to represent an arc.
        But in this logic_solver, we always use two points to represent an arc.
            In that case, the order matters.
        This function aims to do such transformation.
        """
        assert 2 <= len(arc) <= 4
        circle_centers = self.find_all_circles()
        if len(arc) > 2 and arc[0] in circle_centers:
            center = arc[0]
            arc = arc[1:]
        else:
            # No center is specified, so we just randomly assign a center.
            # TODO: multiple circles with the same center.
            center = circle_centers[0]

        # Warning: The order of cross opposites to the normal coordinate system.
        if len(arc) == 2:
            # assume that the angle is always smaller than 180.
            if self.cross(center, arc[0], arc[1]) > 0:
                arc = arc[::-1]  # reverse
        else:
            # usually the angle bigger than 180, but not absolutely.
            if self.cross(arc[0], arc[1], arc[2]) < 0:
                arc = [arc[0], arc[2]]
            else:
                arc = [arc[2], arc[0]]
        return [center] + arc

    def defineLine(self, pointA, pointB, value=None):
        self.define_point([pointA, pointB])
        changed = self.define_line(pointA, pointB)
        if value:
            changed = self.define_length(pointA, pointB, value)
        return changed

    def defineAngle(self, pointA, pointB, pointC, value=None):
        self.define_point([pointA, pointB, pointC])
        self.define_line(pointA, pointB)
        self.define_line(pointB, pointC)
        changed = self.define_angle(pointA, pointB, pointC)
        if value:
            changed = self.define_angle_measure(pointA, pointB, pointC, value)
        return changed

    def defineArc(self, pointO, pointA, pointB, value=None):
        self.define_point([pointO, pointA, pointB])
        changed = self.define_arc(pointO, pointA, pointB)
        if value:
            changed = self.define_arc_measure(pointO, pointA, pointB, value) or changed
        return changed

    def definePolygon(self, points):
        l = len(points)
        for i in range(l):
            self.define_point(points[i])
            self.define_line(points[i], points[(i + 1) % l])
            self.define_angle(points[i], points[(i + 1) % l], points[(i + 2) % l])
        if l == 3:
            facts(self.Triangle, points)
        elif l == 4:
            facts(self.Quadrilateral, points)
        elif l == 5:
            facts(self.Pentagon, points)

    def defineCircle(self, circle, point):
        res = run(1, (), self.PointOnCircle(circle, point))
        if len(res) > 0:
            return False
        self.define_circle(circle)
        self.define_line(circle, point)
        facts(self.PointOnCircle, (circle, point))
        return True

    def newLineSymbol(self, line):
        # Assign the length of one line with a new symbol(expression)
        sym = Symbol("line_" + ''.join([str(ch) for ch in line]))
        self.defineLine(line[0], line[1], sym)
        return sym

    def newAngleSymbol(self, angle):
        # Assign the measure of one angle with a new symbol(expression)
        sym = Symbol("angle_" + ''.join([str(ch) for ch in angle]))
        self.defineAngle(angle[0], angle[1], angle[2], sym)
        return sym

    def newArcSymbol(self, arc):
        # Assign the measure of one arc with a new symbol(expression)
        sym = Symbol("arc_" + ''.join([str(ch) for ch in arc]))
        self.defineArc(arc[0], arc[1], arc[2], sym)
        return sym

    def lineEqual(self, line1, line2):
        # Parse the logic forms with [Equals(LengthOf(Line(..., ...)), LengthOf(Line(..., ...)))]
        self.defineLine(*line1)
        self.defineLine(*line2)
        changed = False
        symbol1 = list(self.find_line_with_length(line1))  # try to find all possible expressions
        symbol2 = list(self.find_line_with_length(line2))
        if symbol1 == [] and symbol2 == []:
            symbol1 = [self.newLineSymbol(line1)]

        # copy each other's expression for line1 and line2
        copy1, copy2 = symbol1.copy(), symbol2.copy()
        for sym in copy2:
            if sym in symbol1: continue
            changed = self.defineLine(line1[0], line1[1], sym) or changed
            symbol1.append(sym)
        for sym in copy1:
            if sym in symbol2: continue
            changed = self.defineLine(line2[0], line2[1], sym) or changed
            symbol2.append(sym)
        return changed

    def angleEqual(self, angle1, angle2):
        # Parse the logic forms with [Equals(Measureof(Angle(..., ...)), MeasureOf(Angle(..., ...)))]
        self.defineAngle(*angle1)
        self.defineAngle(*angle2)
        changed = False
        symbol1 = list(self.find_angle_measure(angle1))
        symbol2 = list(self.find_angle_measure(angle2))
        if symbol1 == [] and symbol2 == []:
            symbol1 = [self.newAngleSymbol(angle1)]

        copy1, copy2 = symbol1.copy(), symbol2.copy()
        for sym in copy2:
            if sym in symbol1: continue
            changed = self.defineAngle(angle1[0], angle1[1], angle1[2], sym) or changed
            symbol1.append(sym)
        for sym in copy1:
            if sym in symbol2: continue
            changed = self.defineAngle(angle2[0], angle2[1], angle2[2], sym) or changed
            symbol2.append(sym)
        return changed

    def arcEqual(self, arc1, arc2):
        # Parse the logic forms with [Equals(Measureof(Arc(..., ...)), MeasureOf(Arc(..., ...)))]
        self.defineArc(*arc1)
        self.defineArc(*arc2)
        changed = False
        symbol1 = list(self.find_angle_measure(arc1))
        symbol2 = list(self.find_angle_measure(arc2))
        if symbol1 == [] and symbol2 == []:
            symbol1 = [self.newArcSymbol(arc1)]

        copy1, copy2 = symbol1.copy(), symbol2.copy()
        for sym in copy2:
            if sym in symbol1: continue
            changed = self.defineArc(arc1[0], arc1[1], arc1[2], sym) or changed
            symbol1.append(sym)
        for sym in copy1:
            if sym in symbol2: continue
            changed = self.defineArc(arc2[0], arc2[1], arc2[2], sym) or changed
            symbol2.append(sym)
        return changed

    def defineSimilarTriangle(self, tri1, tri2):
        self.definePolygon(tri1)
        self.definePolygon(tri2)
        for ch in permutations([0, 1, 2]):
            facts(self.SimilarTriangle, (tri1[ch[0]], tri1[ch[1]], tri1[ch[2]], tri2[ch[0]], tri2[ch[1]], tri2[ch[2]]))
            facts(self.SimilarTriangle, (tri2[ch[0]], tri2[ch[1]], tri2[ch[2]], tri1[ch[0]], tri1[ch[1]], tri1[ch[2]]))

    def defineCongruentTriangle(self, tri1, tri2):
        self.definePolygon(tri1)
        self.definePolygon(tri2)
        for ch in range(3):
            self.lineEqual([tri1[ch], tri1[(ch + 1) % 3]], [tri2[ch], tri2[(ch + 1) % 3]])
        for ch in range(3):
            self.angleEqual([tri1[ch], tri1[(ch + 1) % 3], tri1[(ch + 2) % 3]],
                            [tri2[ch], tri2[(ch + 1) % 3], tri2[(ch + 2) % 3]])

    def put_equal_into_symbol(self):
        """
        Sometimes the logic form is Equals(m, n), but we don't know what m and n exactly mean.
        So we just record all this relations in self.Equal and resolve it before search.
        """
        x = var()
        y = var()
        res = run(0, (x, y), self.Equal(x, y))

        for sym1, sym2 in res:
            if isNumber(sym1) and isNumber(sym2):
                continue
            if isNumber(sym1):
                sym1, sym2 = sym2, sym1
            # self.variable[sym1] = sym2
            nowdict = {sym1: sym2}
            self.variables = {key: value if type(value) in [int, float] else value.subs(nowdict)
                              for key, value in self.variables.items()}
            self.variables.update(nowdict)

    def try_delete_unused_points(self):
        """
        Some points may be useless, so we eliminate these unused points in this function.
        This function can be skipped, but it can accelerate the solver.
        """
        points = self.find_all_points()
        angles = self.find_all_angle_measures()
        f = self.find_all_180_angles(angles)

        lines = self.find_all_lines_with_length()
        saved = [l[0] for l in lines] + [l[1] for l in lines]
        circles = self.find_all_circles()
        saved.extend(circles)
        for circle in circles:
            saved.extend(self.find_points_on_circle(circle))
        for angle in angles:
            saved.append(angle[0])
            saved.append(angle[1])
            saved.append(angle[2])
        del_points = []
        for point in points:
            others = self.find_all_lines_for_point(point)
            is_mid = False
            is_cross = False
            for point1, point2 in combinations(others, 2):
                if not self.is_colinear(point, point1, point2, f):
                    is_cross = True
                    break
                is_mid = is_mid or ((point1, point, point2) in f)
            if not is_cross and is_mid:
                del_points.append(point)
        self.delete_unused_points(list(set(del_points) - set(saved)))

    def delete_unused_points(self, points):
        """
        Delete some points from the graph.
        This function follows by [try_delete_unused_points].
        """
        for i in range(len(self.relations)):
            # print (self.relations[i])
            # print ("facts", self.relations[i].facts)
            # print ("index", self.relations[i].index)
            facts_ = self.relations[i].facts
            self.relations[i].facts = set()
            self.relations[i].index = dict()
            for fact in facts_:
                if all([point not in fact for point in points]):
                    facts(self.relations[i], fact)
            # print ("facts", self.relations[i].facts)
            # print ("index", self.relations[i].index)
        self.points_on_line = {}
        self.lines_for_point = {}
        self.initUni = False

    def init_all_uni_lines(self):
        """
        To find all lines (segments) which can not be divided (No midpoint inside it).
        Use self.UniLine to define them.
        """
        f = self.find_all_180_angles()
        lines = self.find_all_lines()
        points = self.find_all_points()
        for line in lines:
            is_uni = True
            for point in points:
                if (line[0], point, line[1]) in f or (line[1], point, line[0]) in f:
                    is_uni = False
                    break
            if is_uni:
                self.define_uni_line(line[0], line[1])
        self.initUni = True
        self.points_on_line = {}

    def find_hidden_polygons(self, l):
        """
        Find all polygons which may not be mentioned in the logic forms but will be useful when solving.
        """
        x = [var() for i in range(l)]
        if l == 3:
            res = run(0, tuple(x), self.seem_triangle(*x))
        elif l == 4:
            res = run(0, tuple(x), self.seem_quadrilateral(*x))
        else:
            return
        # TODO: l > 4

        polygons = []
        for poly in res:
            poly1 = list(poly)
            poly2 = poly1[::-1]
            id1 = poly1.index(min(poly1))
            id2 = poly2.index(min(poly2))
            polygons.append(min(tuple(poly1[id1:] + poly1[0:id1]), tuple(poly2[id2:] + poly2[0:id2])))
            # Use minimum representation to represent polygons.

        polygons = list(set(polygons))  # Erase the duplicated polygons
        f = self.find_all_180_angles()
        valid = []
        for polygon in polygons:
            is_polygon = True
            set_list = []
            for i in range(l):
                set_list.append(set(self.find_all_points_on_line((polygon[i], polygon[(i + 1) % l]))))
            for i in range(l):
                for j in range(i + 1, l):
                    # Can not belong to the same line
                    if set_list[i] == set_list[j]:
                        is_polygon = False
                    intersection = set_list[i] & set_list[j]
                    # The intersections can only be the vertex on the polygon.
                    for point in intersection:
                        if (polygon[i], point, polygon[(i + 1) % l]) in f or (
                                polygon[j], point, polygon[(j + 1) % l]) in f:
                            is_polygon = False
            if is_polygon:
                self.definePolygon(polygon)
                valid.append(polygon)
        return valid

    def expand_angles(self):
        """
        This function needs to be executed only once, after parsing all the logic forms.
        It will find all the hidden angles and assign each angle with a symbol(expression).
        """
        # First find all 180 angles (These angles should be defined already and can not be expanded).
        angles = self.find_all_angle_measures()
        f = self.find_all_180_angles(angles)

        # Find other angles that can be formed by points and lines.
        points = self.find_all_points()
        lines = self.find_all_lines()
        point2lines = {point: set() for point in points}
        for line in lines:
            point2lines[line[0]].add(line[1])
            point2lines[line[1]].add(line[0])
        remain_angles = []
        for point in points:
            for point1, point2 in combinations(point2lines[point], 2):
                if self.is_colinear(point, point1, point2, f): continue
                remain_angles.append((point1, point, point2))
                remain_angles.append((point2, point, point1))
        angles.extend(list(set(remain_angles)))

        # Start to expand angles: (1) same angles with different ends. (2) vertical angles
        have_set_value = set()
        for angle in angles:
            if len(angle) > 3 and angle[3] == 180: continue  # in the same line
            if angle in have_set_value: continue
            _1 = self.find_all_points_on_line([angle[0], angle[1]])
            _2 = self.find_all_points_on_line([angle[2], angle[1]])
            if angle[2] in _1: continue  # in the same line
            sym = angle[3] if len(angle) > 3 else self.newAngleSymbol(angle)
            for point1, point2 in product(_1, _2):
                if point1 == angle[1] or point2 == angle[1]: continue
                same_side1 = (angle[1], angle[0], point1) in f or (angle[1], point1, angle[0]) in f or point1 == angle[
                    0]
                same_side2 = (angle[1], angle[2], point2) in f or (angle[1], point2, angle[2]) in f or point2 == angle[
                    2]
                if same_side1 != same_side2: continue  # All True: normal angles; All False: vertical angles.

                self.defineAngle(point1, angle[1], point2, sym)
                have_set_value.add((point1, angle[1], point2))
                have_set_value.add((point2, angle[1], point1))

    def set_line_sum(self):
        """
        This function is to build the relations between lines.
        Assign each line segment a symbol if no assigned value
        e.g. If A, B, C are three points in a same line, then we know AC=AB+BC.
        """
        lines = self.find_all_lines()
        have_set = set()
        for line in lines:
            points = self.find_all_points_on_line(line)
            if tuple(points) in have_set: continue
            have_set.add(tuple(points))
            have_set.add(tuple(points[::-1]))
            number = len(points)
            for l in range(1, number):  # l: length of line
                for i in range(0, number - l):
                    point1, point2 = points[i], points[i + l]  # start, end
                    val = self.find_line_with_length((point1, point2))  # e.g., 6, x+21.0
                    if l == 1:
                        # one-segment line
                        if len(val) == 0:
                            self.define_length(point1, point2, self.newLineSymbol((point1, point2)))
                    else:
                        # multiple-segment line
                        val = sum([self.find_line_with_length((points[t], points[t + 1]))[0] for t in range(i, i + l)])
                        self.define_length(point1, point2, val)

    def _possible_angle(self, line0, line1, line2, angle1):
        ok1, ok2 = False, False
        for p, q in product(line0[line0.index(angle1) + 1:], line1[line1.index(angle1) + 1:]):
            if self.check_uni_line((p, q)):
                ok1 = True
                break
        for p, q in product(line2[line2.index(angle1) + 1:], line1[line1.index(angle1) + 1:]):
            if self.check_uni_line((p, q)):
                ok2 = True
        return ok1 and ok2

    def cross(self, p0, p1, p2):
        if self.point_positions is None: return 0
        p0 = self.point_positions[p0]
        p1 = self.point_positions[p1]
        p2 = self.point_positions[p2]
        return (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p2[0] - p0[0]) * (p1[1] - p0[1])

    def pdot(self, p0, p1, p2):
        if self.point_positions is None: return 0
        p0 = self.point_positions[p0]
        p1 = self.point_positions[p1]
        p2 = self.point_positions[p2]
        return (p1[0] - p0[0]) * (p2[0] - p0[0]) + (p1[1] - p0[1]) * (p2[1] - p0[1])

    def set_angle_sum(self):
        """
        This function is to build the relations between angles.
        e.g. If O, A, B, C are four points and OA, OB, OC are three lines, then AOC = AOB + BOC.
        """
        angles = self.find_all_angle_measures()
        for angle in angles:
            points = self.find_all_lines_for_point(angle[1])
            line0 = self.find_all_points_on_line((angle[1], angle[0]))
            line2 = self.find_all_points_on_line((angle[1], angle[2]))
            for point in points:
                if point in line0 or point in line2: continue
                line1 = self.find_all_points_on_line((angle[1], point))
                if line1.index(point) <= line1.index(angle[1]): continue
                if self.point_positions is None: continue

                # Maybe (0, 1, 2) = (0, 1, p) + (p, 1, 2). 
                # But we can not determine the sign is + or -.
                # Use point_positions to determine.
                if self.cross(angle[1], angle[0], point) * self.cross(angle[1], point, angle[2]) > 0 and \
                        self.cross(angle[1], angle[0], point) * self.cross(angle[1], angle[0], angle[2]) > 0:
                    # In this case, (0, 1, 2) = (0, 1, p) + (p, 1, 2).
                    v1 = self.find_angle_measure((angle[0], angle[1], point))
                    v2 = self.find_angle_measure((point, angle[1], angle[2]))
                    # print ("!!", (angle[0], angle[1], point), (point, angle[1], angle[2]), v1[0] + v2[0])
                    self.defineAngle(*angle[0:3], v1[0] + v2[0])

    def _calc_angle(self, arc):
        """
        This function is to calculate the arc measure
        """
        fdis = lambda x, y: ((x[0] - y[0]) ** 2 + (x[1] - y[1]) ** 2) ** 0.5
        length = fdis(self.point_positions[arc[1]], self.point_positions[arc[0]]) * \
                 fdis(self.point_positions[arc[2]], self.point_positions[arc[0]])
        theta = math.acos(self.pdot(*arc) / length) / math.pi * 180.0
        if self.cross(*arc) > 0:  # Opposite to the normal coordinate system.
            theta = 360.0 - theta
        return theta

    def set_arc_sum(self):
        """
        This function is to build the relations between arcs.
        """
        if self.point_positions is None:
            return
        for center in self.find_all_circles():
            points = self.find_points_on_circle(center)
            for x, y in permutations(points, 2):
                val = None
                if self.check_angle((x, center, y)) and self.cross(center, x, y) <= 0:
                    val = self.find_angle_measure((x, center, y))[0]
                self.defineArc(center, x, y, val)

        arcs = self.find_all_arcs()
        for arc in arcs:
            if self.check_line((arc[0], arc[1])) and self.check_line((arc[0], arc[2])):
                try:
                    angle = self.find_angle_measure((arc[1], arc[0], arc[2]))[0]
                except:
                    angle = self.newAngleSymbol((arc[1], arc[0], arc[2]))
                    self.defineAngle(arc[1], arc[0], arc[2], angle)

                # Note that it opposites to the normal coordinate system.
                self.defineArc(*arc, angle if self.cross(*arc) <= 0 else 360 - angle)

        # print (self.fine_all_arc_measures())
        for arc1, arc2 in permutations(arcs, 2):
            if arc1[0] != arc2[0] or arc1[2] != arc2[1]: continue
            # Now we should build an equation like arc(A, C) = arc(A, B) + arc(B, C).
            if arc1[1] == arc2[2]:
                try:
                    self.defineArc(*arc1, 360 - self.find_arc_measure(*arc2)[0])
                except:
                    try:
                        self.defineArc(*arc2, 360 - self.find_arc_measure(*arc1)[0])
                    except:
                        v = self.newArcSymbol(arc1)
                        self.defineArc(*arc1, v)
                        self.defineArc(*arc2, 360 - v)
            elif self._calc_angle(arc1) + self._calc_angle(arc2) < 360.0:
                try:
                    v1 = self.find_arc_measure(arc1)[0]
                except:
                    v1 = self.newArcSymbol(arc1)
                    self.defineArc(*arc1, v1)
                try:
                    v2 = self.find_arc_measure(arc2)[0]
                except:
                    v2 = self.newArcSymbol(arc2)
                    self.defineArc(*arc2, v2)
                self.defineArc(arc1[0], arc1[1], arc2[2], v1 + v2)
