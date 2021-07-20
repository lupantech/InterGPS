from kanren import Relation, facts
from kanren import run, eq, membero, var, conde

from itertools import combinations, permutations, product

class BasicDefinition(object):
    def __init__(self, debug):

        self.Point = Relation()
        self.Line = Relation()
        self.Length = Relation()
        self.UniLine = Relation()
        self.Angle = Relation()
        self.AngleMeasure = Relation()
        self.Arc = Relation()
        self.ArcMeasure = Relation()
        self.Circle = Relation()

        self.PointOnCircle = Relation()
        self.PointLiesOnLine = Relation()
        self.Perpendicule = Relation()
        self.Parallel = Relation()

        self.Triangle = Relation()
        self.Quadrilateral = Relation()
        self.Pentagon = Relation()

        self.Equal = Relation()
        self.SimilarTriangle = Relation()

        self.relations = [
            self.Point,
            self.Line,
            self.Length,
            self.UniLine,
            self.Angle,
            self.AngleMeasure,
            self.Arc,
            self.ArcMeasure,
            self.Circle,

            self.PointOnCircle,
            self.PointLiesOnLine,
            self.Perpendicule,
            self.Parallel,

            self.Triangle,
            self.Quadrilateral,
            self.Pentagon,

            self.Equal,
            self.SimilarTriangle
        ]

        self.variables = dict()
        self.points_on_line = {}
        self.lines_for_point = {}
        self.point_positions = {}
        self.initUni = False
        self.debug = debug

    ############### Definition of Shapes ###############
    def define_equal(self, para1, para2):
        # This function is used to build a bridge between two expressions.
        # If the logic form is Equals(x, y), then we know self.Equal(x, y).
        facts(self.Equal, (para1, para2))

    def define_circle(self, circle):
        facts(self.Circle, circle)

    def define_point(self, points):
        # This function is to define a list of points.
        # [points] can be either a single-letter string, or a list.
        # Return True if a new point is added.
        if type(points) == str:
            points = [points]
        changed = False
        for point in points:
            res = run(1, (), self.Point(point))
            if len(res) == 0:
                changed = True
                facts(self.Point, (point))
        return changed

    def define_line(self, point_A, point_B):
        res = run(1, (), self.Line(point_A, point_B)) # res = () if new p_A and p_B, else ((),)
        if len(res) > 0: # res = ((),)
            return False
        facts(self.Line, (point_A, point_B))
        facts(self.Line, (point_B, point_A))
        return True

    def define_uni_line(self, point_A, point_B):
        facts(self.UniLine, (point_A, point_B))
        facts(self.UniLine, (point_B, point_A))

    def define_length(self, point_A, point_B, value):
        res = run(1, (), self.Length(point_A, point_B, value))
        if len(res) > 0:
            return False
        facts(self.Length, (point_A, point_B, value))
        facts(self.Length, (point_B, point_A, value))
        return True

    def define_angle(self, point_A, point_B, point_C):
        res = run(1, (), self.Angle(point_A, point_B, point_C))
        if len(res) > 0:
            return False
        facts(self.Angle, (point_A, point_B, point_C))
        facts(self.Angle, (point_C, point_B, point_A))
        return True

    def define_angle_measure(self, point_A, point_B, point_C, value):
        res = run(1, (), self.AngleMeasure(point_A, point_B, point_C, value))
        if len(res) > 0:
            return False
        facts(self.AngleMeasure, (point_A, point_B, point_C, value))
        facts(self.AngleMeasure, (point_C, point_B, point_A, value))
        return True

    def define_arc(self, point_O, point_A, point_B):
        # This arc goes from point_A to point_B in a counter-clockwise order.
        res = run(1, (), self.Arc(point_O, point_A, point_B))
        if len(res) > 0:
            return False
        facts(self.Arc, (point_O, point_A, point_B))
        return True

    def define_arc_measure(self, point_O, point_A, point_B, value):
        # This arc goes from point_A to point_B in a counter-clockwise order.
        res = run(1, (), self.ArcMeasure(point_O, point_A, point_B, value))
        if len(res) > 0:
            return False
        facts(self.ArcMeasure, (point_O, point_A, point_B, value))
        return True

    def define_parallel(self, line1, line2):
        # Define two lines parallel
        facts(self.Parallel, (line1[0], line1[1], line2[0], line2[1]))

    def seem_triangle(self, point_A, point_B, point_C):
        return conde((self.Line(point_A, point_B), self.Line(point_B, point_C),  self.Line(point_A, point_C)))

    def seem_quadrilateral(self, point_A, point_B, point_C, point_D):
        return conde((self.Line(point_A, point_B), self.Line(point_B, point_C),  self.Line(point_C, point_D), self.Line(point_D, point_A)))

    def seem_pentagon(self, point_A, point_B, point_C, point_D, point_E):
        return conde((self.Line(point_A, point_B), self.Line(point_B, point_C),  self.Line(point_C, point_D), self.Line(point_D, point_E), self.Line(point_E, point_A)))

    ############### Finding out Attributes ###############
    def find_all_points(self):
        x = var()
        res = run(0, x, self.Point(x))
        return list(res)

    def find_all_lines(self):
        x = var()
        y = var()
        res = run(0, (x,y), self.Line(x, y))
        return list(res)

    def check_line(self, line):
        res = run(1, (), self.Line(line[0], line[1]))
        return len(res) > 0

    def check_uni_line(self, line):
        res = run(1, (), self.UniLine(line[0], line[1]))
        return len(res) > 0

    def check_similar_triangle(self, tri1, tri2):
        res = run(1, (), self.SimilarTriangle(*tri1, *tri2))
        return len(res) > 0

    def check_line_with_length(self, l):
        x, y = var(), var()
        line = run(0, (x, y), self.Length(x, y, l))
        return list(line)

    def find_all_uni_lines(self):
        x = var()
        y = var()
        res = run(0, (x,y), self.UniLine(x, y))
        return list(res)

    def find_line_with_length(self, line, skip_if_has_number = True):
        '''Give a line (segment) and try to find its length.
        Args:
            list_or_tuple(point, point): the specific line.
            skip_if_has_number:
                True: If one of its representations is an exact number, only return this number not the whole list.
                False: Return all the representations in a list.
        Returns:
            A list contains representations for the current line.
        '''
        z = var()
        res = run(0, z, self.Length(line[0], line[1], z)) # try to find the line length
        final = set()  # use to get the unique result
        for val in res:
            try:
                if type(val) in [int, float]:
                    new_val = float(val)
                else:
                    new_val = float(val.evalf(subs=self.variables)) # evalf evaluates the expression to a floating-point number
                if skip_if_has_number:
                    return [new_val]
                final.add(new_val)
            except:
                # e.g., res = x + 21.0, val = x + 21.0
                new_val = val.subs(self.variables) # Substitute multiple symbols with a mapping dict (self.variables)
                final.add(new_val) # e.g., final = {x + 21.0}
        return list(final) # e.g., ['line_CA'], ['x'], ['line_CA+x']

    def find_all_lines_with_length(self):
        '''Find all lines in the graph with their length.'''
        lines = self.find_all_lines()
        res = []
        for line in lines:
            val = self.find_line_with_length(line)
            if len(val) > 0:
                res.append((line[0], line[1], val[0]))
        return res

    def find_points_on_circle(self, circle):
        x = var()
        res = run(0, x, self.PointOnCircle(circle, x))
        return list(res)

    def find_all_circles(self):
        x = var()
        res = run(0, x, self.Circle(x))
        return list(res)

    def check_angle(self, angle):
        res = run(0, (), self.Angle(angle[0], angle[1], angle[2]))
        return len(res) > 0

    def check_angle_measure(self, angle):
        res = run(0, (), self.AngleMeasure(*angle))
        return len(res) > 0

    def find_all_angles(self):
        x = var()
        y = var()
        z = var()
        res = run(0, (x,y,z), self.Angle(x,y,z))
        return list(res)

    def find_angle_measure(self, angle, skip_if_has_number = True):
        '''Give an angle and try to find its measure.
        Args:
            list_or_tuple(point, point, point): the specific angle.
            skip_if_has_number:
                True: If one of its representations is an exact number, only return this number not the whole list.
                False: Return all the representations in a list.
        Returns:
            A list contains representations for the current angle.
        '''
        z = var()
        res = run(0, z, self.AngleMeasure(angle[0], angle[1], angle[2], z))
        final = set()
        for val in res:
            try:
                if type(val) in [int, float]:
                    new_val = float(val)
                else:
                    new_val = float(val.evalf(subs=self.variables))
                if skip_if_has_number:
                    return [new_val]
                final.add(new_val)
            except:
                new_val = val.subs(self.variables)
                final.add(new_val)
        return list(final)

    def find_all_angle_measures(self):
        x = var()
        y = var()
        z = var()
        # w = var()
        # res = run(0, (x,y,z,w), self.AngleMeasure(x,y,z,w))
        # return sorted(list(res), key = lambda x: str(x[3]))
        res = []
        angles = self.find_all_angles()
        for angle in angles:
            vals = self.find_angle_measure(angle)
            for val in vals:
                res.append((*angle, val))
        return res


    def find_all_180_angles(self, angles = None):
        if angles == None:
            angles = self.find_all_angle_measures()
        f={}
        for angle in angles:
            if angle[3] == 180:
                f[(angle[0], angle[1], angle[2])] = True
                # the reverse (2,1,0) will be enumerated, too.
        return f

    def find_all_90_angles(self, angles = None):
        if angles == None:
            angles = self.find_all_angle_measures()
        f={}
        for angle in angles:
            if angle[3] == 90:
                f[(angle[0], angle[1], angle[2])] = True
                # the reverse (2,1,0) will be enumerated, too.
        return f

    def find_all_arcs(self):
        x, y, z = var(), var(), var()
        res = run(0, (x, y, z), self.Arc(x, y, z))
        return list(res)

    def find_arc_measure(self, arc, skip_if_has_number = True):
        '''Give an arc and try to find its measure.
        Args:
            list_or_tuple(point, point, point): the specific arc.
            skip_if_has_number:
                True: If one of its representations is an exact number, only return this number not the whole list.
                False: Return all the representations in a list.
        Returns:
            A list contains representations for the current angle.
        '''
        z = var()
        res = run(0, z, self.ArcMeasure(*arc, z))
        final = set()
        for val in res:
            try:
                if type(val) in [int, float]:
                    new_val = float(val)
                else:
                    new_val = float(val.evalf(subs=self.variables))
                if skip_if_has_number:
                    return [new_val]
                final.add(new_val)
            except:
                new_val = val.subs(self.variables)
                final.add(new_val)
        return list(final)

    def fine_all_arc_measures(self):
        x, y, z, w = var(), var(), var(), var()
        res = run(0, (x, y, z, w), self.ArcMeasure(x, y, z, w))
        return list(res)

    def find_all_lines_for_point(self, point):
        '''
        Find all points that link to the current point.
        To accelerate this process, the result will be recorded in [self.lines_for_point].
        '''
        if point in self.lines_for_point:
            return self.lines_for_point[point]
        lines = self.find_all_lines()
        self.lines_for_point[point] = [line[0] for line in lines if line[1] == point]
        return self.lines_for_point[point]

    def is_colinear(self, pointA, pointB, pointC, f):
        # check that whether pointA, pointB, pointC is colinear.
        # f is a dict which contains all 180 angles.
        assert isinstance(f, dict)
        return (pointA, pointB, pointC) in f or \
               (pointB, pointA, pointC) in f or \
               (pointA, pointC, pointB) in f

    def find_all_points_on_line(self, line):
        '''
        Given line, find all the points on this line in the increasing order if [self.initUni = True].
        e.g.    A, B, C, D are four points in a same line.
                Give: line = [D, B]
                Returns: [D, C, B, A]

        If we call this function when [self.initUni = False] (which means we haven't prepared all the uni-lines),
        we can also acquire these points but the order can not be guaranteed.
        '''
        line = tuple(line)
        # Accelerate
        if line in self.points_on_line:
            return self.points_on_line[line]

        points = self.find_all_points()
        angles = self.find_all_angle_measures()
        f = self.find_all_180_angles(angles)

        # Try to find all the points on the line
        Update = True
        now_points = [line[0], line[1]]
        while Update:
            Update = False
            for point in set(points)-set(now_points):
                # check whether [point] can be added into the current list.
                for point1, point2 in combinations(now_points, 2):
                    if self.is_colinear(point1, point, point2, f):
                        now_points.append(point)
                        Update = True
                        break
                if Update: break  # avoid adding duplicate points in out list.

        # Try to sort the line with increasing order.
        if self.initUni:
            new_list = [line[0]]
            while len(new_list) < len(now_points):
                changed = False
                for point in now_points:
                    if not point in new_list:
                        if self.check_uni_line((point, new_list[-1])):
                            new_list.append(point)
                            changed = True
                        elif self.check_uni_line((point, new_list[0])):
                            new_list = [point] + new_list
                            changed = True
                if not changed:
                    print("\033[0;0;41mError:\033[0m ", end = "")
                    print ("the line information is incorrect.")
                    print (now_points, new_list)
                    new_list = now_points
                    break
        else:
            new_list = now_points

        for p1, p2 in combinations(new_list, 2):
            # Change the direction if possible.
            if new_list.index(p1) > new_list.index(p2):
                p1, p2 = p2, p1
            # Store the answer to accelerate
            self.points_on_line[(p1, p2)] = new_list
            self.points_on_line[(p2, p1)] = new_list[::-1]

        return self.points_on_line[line]

    def find_all_triangles(self):
        x = var()
        y = var()
        z = var()

        res = run(0, (x, y, z), self.Triangle(x, y, z))
        return list(res)

    def find_all_quadrilaterals(self):
        x = var()
        y = var()
        z = var()
        w = var()

        res = run(0, (x, y, z, w), self.Quadrilateral(x, y, z, w))
        return list(res)

    def find_all_pentagons(self):
        x = var()
        y = var()
        z = var()
        s = var()
        t = var()

        res = run(0, (x, y, z, s, t), self.Pentagon(x, y, z, s, t))
        return list(res)

    def find_all_parallels(self):
        x = var()
        y = var()
        z = var()
        w = var()

        res = run(0, (x,y,z,w), self.Parallel(x,y,z,w))
        return [((t[0], t[1]), (t[2], t[3])) for t in res]
