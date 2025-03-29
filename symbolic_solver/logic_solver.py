import math
import random

from utils import isNumber, hasNumber, heron_triangle_formula, angle_area_formula

from sympy import Symbol, Number
from sympy import cos, sin, pi, solve, nonlinsolve, nsolve

from itertools import permutations, product, combinations

from func_timeout import func_timeout, FunctionTimedOut

class LogicSolver:
    def __init__(self, logic):
        self.logic = logic
        self.can_search = False
        self.hasSolution = False
        self.equations = []
        self.function_maps = {1: self.func1_direct_triangle_sum_theorem, 2: self.func2_indirect_triangle_sum_theorem,
                       3: self.func3_isosceles_triangle_theorem_line, 4: self.func4_isosceles_triangle_theorem_angle,
                       5: self.func5_congruent_triangles_theorem_line, 6: self.func6_congruent_triangles_theorem_angle,
                       7: self.func7_radius_equal_theorem, 8: self.func8_tangent_radius_theorem,
                       9: self.func9_center_and_circumference_angle, 10: self.func10_parallel_lines_theorem,
                       11: self.func11_flat_angle_theorem, 12: self.func12_intersecting_chord_theorem,
                       13: self.func13_polygon_interior_angles_theorem, 14: self.func14_similar_triangle_theorem,
                       15: self.func15_angle_bisector_theorem, 16: self.func16_cosine_theorem,
                       17: self.func17_sine_theorem};
        self.interval = 11
        # <= interval: Propagate;   > interval: Build Equations.
        self.sympy_solver_time_limit = 20 
        # sympy solver time limit in seconds

    @staticmethod
    def _triangleEqual(length, angle, original_angle):
        """
        Please consider the order in the parameters
        length[0..5](Boolean)   length[ch]<->length[ch+3]
        angle[0..5] (Boolean)   angle[ch] <-> angle[ch+3]
        The order of original_angle[0..5](list) matters.
        """
        if sum(length) >= 3 or sum(length) >= 1 and sum(angle) >= 2:
            return True  # SSS or AAS
        if sum(length) >= 2 and sum(angle) == 1:
            if all([angle[0], length[0], length[1]]) or all([angle[1], length[0], length[2]]) or all(
                    [angle[2], length[0], length[1]]):
                return True  # SAS
            id = angle.index(True)
            if 90 in original_angle[id] or 90 in original_angle[id + 3]:
                return True  # HL
        return False

    @staticmethod
    def _traingleSimilar(angle):
        return sum(angle) >= 2

    @staticmethod
    def _hasSymbol(expr):
        if type(expr) in [int, float]:
            return False
        return len(expr.free_symbols) > 0

    @staticmethod
    def _generateAngles(tri):
        return [(tri[0], tri[2], tri[1]), (tri[0], tri[1], tri[2]), (tri[1], tri[0], tri[2])]

    @staticmethod
    def _generateLines(tri):
        return [(tri[0], tri[1]), (tri[0], tri[2]), (tri[1], tri[2])]

    @staticmethod
    def _isComplex(st):
        return st.find("sin") != -1 or st.find("cos") != -1 or st.find("**2") != -1 or st.find("sqrt") != -1

    @staticmethod
    def _isTrig(st):
        return st.find("sin") != -1 or st.find("cos") != -1

    @staticmethod
    def _same(list1, list2):
        return any([pair[0] == pair[1] for pair in product(list1, list2)])

    def _isPrimitive(self, expr):
        return self._hasSymbol(expr) and all([str(expr).find(t) == -1 for t in ['+', '-', '*', '/', '(', ')', '**', 'sqrt']])

    def Solve_Equations(self):
        # add equations for angles, lines and arcs
        for line in self.logic.find_all_lines():
            lst = self.logic.find_line_with_length(line, skip_if_has_number=False)  # [line_CX + line_XD, 24.0]
            for i in range(1, len(lst)):
                # print ("[equations] line equations", line, lst[i-1], lst[i])
                self.equations.append(lst[i] - lst[i - 1])
        for angle in self.logic.find_all_angles():
            lst = self.logic.find_angle_measure(angle, skip_if_has_number=False)
            # [angle_ODC, -angle_COD - angle_ODC + 180, angle_OCD]
            for i in range(1, len(lst)):
                # print ("[equations] angle equations", angle, lst[i-1], lst[i], lst[i] - lst[i-1])
                self.equations.append(lst[i] - lst[i - 1])
        for arc in self.logic.find_all_arcs():  # arc = ('O', 'B', 'C')
            lst = self.logic.find_arc_measure(arc, skip_if_has_number=False)  # [360 - arc_OCB, angle_BOC, arc_OBC]
            for i in range(1, len(lst)):
                # print ("[equations] arc equations", angle, lst[i-1], lst[i])
                self.equations.append(lst[i] - lst[i - 1])

        # simplify, discard the equations which are nan or float or int
        self.equations = [expr.simplify() for expr in self.equations if self._hasSymbol(expr)]
        self.equations = [expr for expr in self.equations if self._hasSymbol(expr)]
        self.equations = list(set(self.equations))  # remove redundant equations quickly
        self.equations, temp_equations = [], self.equations
        
        # Bad idea: the strategy below for avoiding duplicated equations by using "mp" to store the used symbols.
        # This idea will remove valuable equations for multivariate equation group, which should not be adopted.
        # mp = []
        for equation in temp_equations:
            if not type(equation) in [float, int] and len(equation.free_symbols) > 0:  # unknown variables
                symbols = set(equation.free_symbols)  # {line_XD, line_CX} # symbols: unknown variables in the equation
                # if symbols in mp: continue
                # New Feature: Avoid duplicated equations. # TODO BUG ???

                def discard_zero(t):
                    return 0.0 if abs(t) <= 1e-15 else t
                self.equations.append(equation.xreplace({n: discard_zero(n) for n in equation.atoms(Number)}))
                # mp.append(symbols)  # mp = [{line_XD, line_CX}, {angle_BOC, arc_OBC}, ...

        # simplify, discard the equations which are nan or float or int
        self.equations = [expr.simplify() for expr in self.equations if self._hasSymbol(expr)]
        # for e in self.equations:
        #     if not self._isTrig(e):
        #         selected_equations.append(e)

        # for e in selected_equations:
        #     free = list(e.free_symbols)
        #     for f in free:
        #         selected_symbols.add(f)

        # if len(selected_symbols) == len(total_symbols):
        #     self.equations = selected_equations

        # if len(res) > 0 :
        #     print('nonlinesolve',res[0])

        if len(self.equations) == 0:
            return False

        # collect the equations with only 1 free symbol
        symbol2equations ={}
        total_symbols = set()
        for e in self.equations:
            free = list(e.free_symbols)
            if len(free) == 1:
                for f in free:
                    cnt_terms = len(e.as_ordered_terms())
                    if cnt_terms == 1:
                        continue
                    total_symbols.add(f)
                    if f in symbol2equations:
                        symbol2equations[f].append(e)
                    else:
                        symbol2equations[f] = [e]

        # pick a simple equation for each symbol (which have 1-symbol equations) 
        symbol2eq = {}
        for sym,eqs in symbol2equations.items():
            for e in eqs:
                if not self._isComplex(str(e)) :
                    symbol2eq[sym] = e
                    break

        for sym in total_symbols:
            if sym not in symbol2eq and sym in symbol2equations:
                estimate = lambda e: len(e.as_ordered_terms()) + 0.5 * self._isTrig(str(e))
                eq = min(symbol2equations[sym], key=estimate)
                symbol2eq[sym] = eq

        # adopt the simple equations to solve (if we have some symbols which have 1-symbol equations)
        if len(symbol2eq) != 0:
            self.equations = list(symbol2eq.values())

        if self.logic.debug:
            print("Try to solve: ", self.equations)

        # solutions1 = solve(self.equations, dict=True, manual=True)  # do not use the polys/matrix method
        try:
            solutions1 = func_timeout(self.sympy_solver_time_limit, solve, kwargs=dict(f=self.equations, dict=True, manual=True))
        except FunctionTimedOut:
            # if self.logic.debug:
            print(repr(e), "on sympy.solve")
            solutions1 = []
            # raise TimeoutError

        complexity = sum([self._isComplex(str(t)) for t in self.equations])
        if complexity <= 3:
            # solutions2 = solve(self.equations, dict = True, manual = False)
            try:
                solutions2 = func_timeout(self.sympy_solver_time_limit, solve, kwargs=dict(f=self.equations, dict=True, manual=False))
            except FunctionTimedOut as e:
                # if self.logic.debug:
                print(repr(e), "on sympy.solve")
                solutions2 = []
                # raise TimeoutError
        else:
            solutions2 = []
            
        # discard the negative sol value for the symbol which is more than 1 letter (e.g. angle_ABC), but keep negative value for the symbol which is 1-letter-symbol (e.g. x, y, z).
        solutions1_ = [sol for sol in solutions1 if not any([len(str(key)) > 1 and isNumber(value) and value <= 0 for key, value in sol.items()])]
        solutions2_ = [sol for sol in solutions2 if not any([len(str(key)) > 1 and isNumber(value) and value <= 0 for key, value in sol.items()])]

        solutions = solutions1_ if len(solutions1_) > len(solutions2_) else solutions2_

        if len(solutions) == 0:
            total_symbols = set()
            for e in self.equations:
                if self._hasSymbol(e):
                    free = list(e.free_symbols)
                    for f in free:
                        total_symbols.add(f)
            total_symbols = list(total_symbols)
            if len(total_symbols) > 0:
                # res = list(nonlinsolve(list(self.equations), total_symbols) )
                try:
                    res = list(func_timeout(self.sympy_solver_time_limit, nonlinsolve, args=(list(self.equations), total_symbols)))
                except FunctionTimedOut as e:
                    #if self.logic.debug:
                    print(repr(e), "on sympy.nonlinsolve")
                    # raise TimeoutError

                if len(res) > 0:
                    for j in range(len(res)):
                        sol = dict()
                        for i in range(len(total_symbols)):
                            # print(total_symbols[i])
                            # print( list(res[j])[i])
                            if total_symbols[i] != list(res[j])[i]:
                                sol[total_symbols[i]] = list(res[j])[i]
                        solutions.append(sol)
                else:
                    # try to use numerical solver sympy.nsolve
                    sol_ok = True
                    try:
                        init_guess=[]
                        for i in range(len(total_symbols)):
                            init_guess.append(0.1)
                        res = func_timeout(self.sympy_solver_time_limit, nsolve, args=(list(self.equations), total_symbols,init_guess)).tolist()
                        if len(res) > 0:
                            for i in range(len(total_symbols)):
                                if total_symbols[i] != res[i][0]:
                                        if not res[i][0].is_real:
                                            sol_ok = False
                                            break

                    except FunctionTimedOut as e:
                        print(repr(e), "on sympy.nsolve")
                        sol_ok = False
                        #raise TimeoutError
                    except NotImplementedError as nie:
                        print(repr(nie), "on sympy.nsolve")
                        sol_ok = False
                    except ValueError as e:
                        print(repr(e), "on sympy.nsolve")
                        sol_ok=False
                        if (repr(e)=="ValueError('matrix is not positive-definite')"):
                            raise e

                    # give more chances for numerical solver sympy.nsolve with different init guess
                    if not sol_ok:
                        res = []
                        cnt=30
                        while(len(res) <= 0 and cnt > 0 and not sol_ok):
                            cnt -= 1
                            init_guess = []
                            for i in range(len(total_symbols)):
                                # random guess
                                init_guess.append(random.uniform(-100, 100))
                            try:
                                res = func_timeout(self.sympy_solver_time_limit, nsolve, args=(list(self.equations), total_symbols, init_guess)).tolist()
                            except FunctionTimedOut as e:
                                #if self.logic.debug:
                                print(repr(e), "on sympy.nsolve")
                                break
                            except NotImplementedError as nie:
                                if self.logic.debug:
                                    print(repr(nie), "on sympy.nsolve")
                                break
                            except ValueError as ee:
                                if self.logic.debug:
                                    print(repr(ee), "on sympy.nsolve")
                                continue

                            if len(res) > 0:
                                sol_ok = True
                                for i in range(len(total_symbols)):
                                    if total_symbols[i] != res[i][0]:
                                        if not res[i][0].is_real:
                                            sol_ok = False
                                            break

                    if len(res) > 0:
                        sol = dict()
                        sol_ok = True
                        for i in range(len(total_symbols)):
                            if total_symbols[i] != res[i][0]:
                                # if res[i][0] is complex number, we should discard it.
                                if len(res[i][0].free_symbols)==0:
                                    if res[i][0].is_real:
                                        sol[total_symbols[i]] = res[i][0]
                                    else:
                                        sol_ok = False
                                        break

                                sol[total_symbols[i]] = res[i][0]
                        if sol_ok:
                            solutions.append(sol)

        # discard the solution value with Image Number 'I'
        solutions = [sol for sol in solutions if not any([str(val).find('*I') != -1 for val in sol.values()])]

        if len(solutions) >= 1:
            # Handle with multiple solution
            estimate = lambda sol: sum([str(expr)[0] != '-' for expr in sol.values()])  # negative value
            solution = max(solutions, key=estimate)  # we like a solution with less negative values :)
            nowdict = {}
            if self.logic.debug:
                print("Solve out: ", solution)
            for key, value in solution.items():
                # if str(value)[0] == '-' and not '+' in str(value):
                #     # the expression may be negative by solve the square equations.d
                #     # sympy can not give all the solutions, so we should change its sign manually...
                #     #print ("Warning! Change sign(", key, ", ", value, ')')
                #     value = -value
                assert self.logic.variables.get(key, value) == value
                nowdict[key] = value
            self.hasSolution = True
            self.logic.variables = {key: value if type(value) in [int, float] else value.subs(nowdict)
                                    for key, value in self.logic.variables.items()}
            # We may substitute the key in the previous dict further.
            self.logic.variables.update(nowdict)
            return True
        self.hasSolution = len(self.equations) == 0
        return False

    def func1_direct_triangle_sum_theorem(self):
        Update = False
        triangles = self.logic.find_all_triangles()
        for tri in triangles:
            angles = self._generateAngles(tri)
            measures = [self.logic.find_angle_measure(x) for x in angles]
            unknowns = [i for i in range(3) if not hasNumber(measures[i])]
            if 1 <= len(unknowns) <= 2:
                idx = unknowns[0]
                other1, other2 = measures[(idx + 1) % 3][0], measures[(idx + 2) % 3][0]
                Update = self.logic.define_angle_measure(*angles[idx], 180 - other1 - other2) or Update
        return Update

    def func2_indirect_triangle_sum_theorem(self):
        # The sum of three angles in a triangle is 180
        Update = False
        triangles = self.logic.find_all_triangles()
        for tri in triangles:
            angles = self._generateAngles(tri)
            measures = [self.logic.find_angle_measure(x) for x in angles]
            self.equations.append(measures[0][0] + measures[1][0] + measures[2][0] - 180)
            unknowns = [i for i in range(3) if not hasNumber(measures[i])]
            if len(unknowns) == 3:
                Update = self.logic.define_angle_measure(*angles[0], 180 - measures[1][0] - measures[2][0]) or Update
        return Update

    def func3_isosceles_triangle_theorem_line(self):
        Update = False
        triangles = self.logic.find_all_triangles()
        for tri in triangles:
            angles = self._generateAngles(tri)
            measures = [self.logic.find_angle_measure(x) for x in angles]
            lines = self._generateLines(tri)
            for ch in permutations([0, 1, 2]):
                if self._same(measures[ch[0]], measures[ch[1]]):
                    Update = self.logic.lineEqual(lines[ch[0]], lines[ch[1]]) or Update
                    line_measures = [self.logic.find_line_with_length(x) for x in [lines[ch[0]], lines[ch[1]]]]
                    self.equations.append(line_measures[0][0] - line_measures[1][0])
        return Update

    def func4_isosceles_triangle_theorem_angle(self):
        # The base angles of a isosceles triangle is equal.
        Update = False
        triangles = self.logic.find_all_triangles()
        for tri in triangles:
            angles = self._generateAngles(tri)
            lines = self._generateLines(tri)
            length = [self.logic.find_line_with_length(x) for x in lines]
            for ch in permutations([0, 1, 2]):
                if self._same(length[ch[0]], length[ch[1]]):
                    Update = self.logic.angleEqual(angles[ch[0]], angles[ch[1]]) or Update
                    angle_measures = [self.logic.find_angle_measure(x) for x in [angles[ch[0]], angles[ch[1]]]]
                    self.equations.append(angle_measures[0][0] - angle_measures[1][0])
        return Update

    def func5_congruent_triangles_theorem_line(self):
        Update = False
        triangles = self.logic.find_all_triangles()
        comb = combinations(triangles, 2)
        for pair in comb:
            # Accelerate
            if set(pair[0]) == set(pair[1]): continue
            for tri1 in permutations(pair[0]):
                tri2 = pair[1]
                lines = self._generateLines(tri1) + self._generateLines(tri2)
                length = [self.logic.find_line_with_length(x) for x in lines]
                angles = [self.logic.find_angle_measure(x) for x in
                          self._generateAngles(tri1) + self._generateAngles(tri2)]
                s = self._same
                same_length = [s(length[0], length[3]), s(length[1], length[4]), s(length[2], length[5])]
                same_angle = [s(angles[0], angles[3]), s(angles[1], angles[4]), s(angles[2], angles[5])]
                if self._triangleEqual(same_length, same_angle, angles):
                    for ch in range(3):
                        Update = self.logic.lineEqual(lines[ch], lines[ch + 3]) or Update
                        line_measure_pair = [self.logic.find_line_with_length(x) for x in [lines[ch], lines[ch + 3]]]
                        self.equations.append(line_measure_pair[0][0] - line_measure_pair[1][0])
        return Update

    def func6_congruent_triangles_theorem_angle(self):
        Update = False
        triangles = self.logic.find_all_triangles()
        comb = combinations(triangles, 2)
        for pair in comb:
            # Accelerate
            if set(pair[0]) == set(pair[1]): continue
            for tri1 in permutations(pair[0]):
                tri2 = pair[1]
                lines = self._generateLines(tri1) + self._generateLines(tri2)
                length = [self.logic.find_line_with_length(x) for x in lines]
                angles = [self.logic.find_angle_measure(x) for x in
                          self._generateAngles(tri1) + self._generateAngles(tri2)]
                s = self._same
                same_length = [s(length[0], length[3]), s(length[1], length[4]), s(length[2], length[5])]
                same_angle = [s(angles[0], angles[3]), s(angles[1], angles[4]), s(angles[2], angles[5])]
                if self._triangleEqual(same_length, same_angle, angles):
                    for ch in range(3):
                        Update = self.logic.angleEqual(self._generateAngles(tri1)[ch],
                                                       self._generateAngles(tri2)[ch]) or Update
                        self.equations.append(angles[ch][0] - angles[ch + 3][0])

        return Update

    def func7_radius_equal_theorem(self):
        Update = False
        circles = self.logic.find_all_circles()
        for circle in circles:
            points = self.logic.find_points_on_circle(circle)
            if len(points) > 1:
                # The length of each radius is same.
                for i in range(len(points) - 1):
                    Update = self.logic.lineEqual((circle, points[i]), (circle, points[i + 1])) or Update
                    line_measure_pair = [self.logic.find_line_with_length(x) for x in [(circle, points[i]), (circle, points[i + 1])]]
                    self.equations.append(line_measure_pair[0][0] - line_measure_pair[1][0])

        return Update

    def func8_tangent_radius_theorem(self):
        Update = False
        circles = self.logic.find_all_circles()
        for circle in circles:
            points = self.logic.find_points_on_circle(circle)
            for p1, p2, p3 in permutations(points, 3):
                if self.logic.find_angle_measure((p1, circle, p3))[0] == 180 and self.logic.check_angle((p1, p2, p3)):
                    Update = self.logic.define_angle_measure(p1, p2, p3, 90) or Update
        return Update

    def func9_center_and_circumference_angle(self):
        Update = False
        circles = self.logic.find_all_circles()
        for center in circles:
            points = self.logic.find_points_on_circle(center)
            for x, y, z in permutations(points, 3):
                if self.logic.cross(center, x, y) > 0: continue
                if all([self.logic.check_line((p, q)) for p, q in [(x, z), (y, z)]]):
                    if self.logic.cross(x,y,z) <=0: # z is on the major arc yx
                        center_angle = self.logic.find_arc_measure((center, x, y))[0]
                        Update = self.logic.defineAngle(x, z, y, 0.5 * center_angle) or Update
                        center_angle = self.logic.find_angle_measure((x, center, y))[0]
                        Update = self.logic.defineAngle(x, z, y, 0.5 * center_angle) or Update

                        angle_measure = self.logic.find_angle_measure((x, z, y))
                        certer_angle_measure = self.logic.find_angle_measure((x, center, y))
                        self.equations.append(angle_measure[0] - 0.5 * certer_angle_measure[0])
                        certer_angle_measure = self.logic.find_arc_measure((center, x, y))
                        self.equations.append(angle_measure[0] - 0.5 * certer_angle_measure[0])

                    else: # z is on the minor arc xy
                        center_angle = self.logic.find_arc_measure((center, y, x))[0]
                        Update = self.logic.defineAngle(x, z, y, 0.5 * center_angle) or Update
                        center_angle = self.logic.find_angle_measure((x, center, y))[0]
                        Update = self.logic.defineAngle(x, z, y, 180 - 0.5 * center_angle) or Update

                        angle_measure = self.logic.find_angle_measure((x, z, y))
                        certer_angle_measure = self.logic.find_arc_measure((center, y, x))
                        self.equations.append(angle_measure[0] - 0.5 * certer_angle_measure[0])
                        certer_angle_measure = self.logic.find_angle_measure((x, center, y))
                        self.equations.append(angle_measure[0] + 0.5 * certer_angle_measure[0] - 180)

        return Update

    def func10_parallel_lines_theorem(self):
        Update = False
        parallels = self.logic.find_all_parallels()
        for line1, line2 in parallels:
            # If the line is represented by symbol, we should change it to two points.
            line1, line2 = self.logic.parseLine(line1), self.logic.parseLine(line2)

            # We want to figure out the order of the parallel lines.
            if self.logic.point_positions is not None:
                fdis = lambda x, y: (x[0] - y[0]) ** 2 + (x[1] - y[1]) ** 2
                dismax, idp, idq = 0, None, None
                for p, q in product(line1, line2):
                    nowdis = fdis(self.logic.point_positions[p], self.logic.point_positions[q])
                    if nowdis > dismax:
                        dismax = nowdis
                        idp, idq = p, q
                if line1.index(idp) == line2.index(idq):
                    line1 = line1[::-1]

            # Now start to use Parallel Theorems
            A = self.logic.find_all_points_on_line(line1)
            B = self.logic.find_all_points_on_line(line2)
            for p, q in product(A, B):
                if not self.logic.check_line((p, q)): continue
                angles = [(A[0], p, q), (A[-1], p, q), (B[0], q, p), (B[-1], q, p)]
                measures = [self.logic.find_angle_measure(x) for x in angles]
                # It is guaranteed that all the angle has at least one symbol.
                if A[0] != p and B[-1] != q:
                    Update = self.logic.angleEqual(angles[0], angles[3]) or Update
                    self.equations.append(measures[0][0] - measures[3][0])
                if A[-1] != p and B[0] != q:
                    Update = self.logic.angleEqual(angles[1], angles[2]) or Update
                    self.equations.append(measures[1][0] - measures[2][0])
                if A[0] != p and B[0] != q:
                    Update = self.logic.define_angle_measure(*angles[0], 180 - measures[2][0]) or Update
                    self.equations.append(measures[0][0] + measures[2][0] - 180)
                if A[-1] != p and B[-1] != q:
                    Update = self.logic.define_angle_measure(*angles[1], 180 - measures[3][0]) or Update
                    self.equations.append(measures[1][0] + measures[3][0] - 180)
        return Update

    def func11_flat_angle_theorem(self):
        # If point O lies on segment (A, B), then AOC + COB = 180.
        Update = False
        angles = self.logic.find_all_angle_measures()
        for angle in angles:
            if angle[3] != 180: continue
            points = set(self.logic.find_all_lines_for_point(angle[1])) - \
                     set(self.logic.find_all_points_on_line((angle[0], angle[2])))
            for point in points:
                val = self.logic.find_angle_measure((point, angle[1], angle[2]))[0]
                Update = self.logic.define_angle_measure(angle[0], angle[1], point, 180 - val) or Update
                angle_measures = [self.logic.find_angle_measure(x) for x in [(angle[0], angle[1], point), (point, angle[1], angle[2])]]
                self.equations.append(angle_measures[0][0] + angle_measures[1][0] - 180)

        return Update

    def func12_intersecting_chord_theorem(self):
        circles = self.logic.find_all_circles()
        for center in circles:
            points = self.logic.find_points_on_circle(center)
            for p1, p2, p3, p4 in permutations(points, 4):
                if self.logic.check_line((p1, p2)) and self.logic.check_line((p3, p4)):
                    intersection = set(self.logic.find_all_points_on_line((p1, p2))) & \
                                   set(self.logic.find_all_points_on_line((p3, p4)))
                    if len(intersection) != 1: continue
                    inter = intersection.pop()
                    l1, l2, l3, l4 = map(self.logic.find_line_with_length,
                                         [(p1, inter), (p2, inter), (p3, inter), (p4, inter)])
                    expr = l1[0] * l2[0] - l3[0] * l4[0]
                    if len(expr.free_symbols) <= 2:
                        self.equations.append(expr)

    def func13_polygon_interior_angles_theorem(self):
        # Equations in Quadrilateral
        Quadrilaterals = self.logic.find_all_quadrilaterals()
        for quad in Quadrilaterals:
            reflex = self.reflex_angle(quad)
            expr1 = sum(
                [self.logic.find_angle_measure((quad[i], quad[(i + 1) % 4], quad[(i + 2) % 4]))[0]
                 for i in range(4) if quad[(i + 1) % 4] not in reflex])
            expr2 = sum(
                [360 - self.logic.find_angle_measure((quad[i], quad[(i + 1) % 4], quad[(i + 2) % 4]))[0]
                 for i in range(4) if quad[(i + 1) % 4] in reflex])
            self.equations.append(expr1 + expr2 - 180 * (len(quad) - 2))
        # Equations in Pentagon
        Pentagons = self.logic.find_all_pentagons()
        for pent in Pentagons:
            reflex = self.reflex_angle(pent)
            expr1 = sum(
                [self.logic.find_angle_measure((pent[i], pent[(i + 1) % 5], pent[(i + 2) % 5]))[0]
                    for i in range(5) if pent[(i + 1) % 5] not in reflex])
            expr2 = sum(
                [360 - self.logic.find_angle_measure((pent[i], pent[(i + 1) % 5], pent[(i + 2) % 5]))[0]
                    for i in range(5) if pent[(i + 1) % 5] in reflex])
            self.equations.append(expr1 + expr2 - 180 * (len(pent) - 2))

    def func14_similar_triangle_theorem(self):
        triangles = self.logic.find_all_triangles()
        comb = combinations(triangles, 2)
        for pair in comb:
            # Accelerate
            if set(pair[0]) == set(pair[1]): continue
            for tri1 in permutations(pair[0]):
                tri2 = pair[1]
                lines = self._generateLines(tri1) + self._generateLines(tri2)
                length = [self.logic.find_line_with_length(x) for x in lines]
                angles = [self.logic.find_angle_measure(x) for x in
                          self._generateAngles(tri1) + self._generateAngles(tri2)]
                s = self._same
                same_angle = [s(angles[0], angles[3]), s(angles[1], angles[4]), s(angles[2], angles[5])]
                if self._traingleSimilar(same_angle) or self.logic.check_similar_triangle(tri1, tri2):
                    for ch1, ch2 in combinations([0, 1, 2], 2):
                        if sum([hasNumber(x) for x in
                                [length[ch1], length[ch1 + 3], length[ch2], length[ch2 + 3]]]) >= 2:
                            expr = length[ch1][0] * length[ch2 + 3][0] - length[ch2][0] * length[ch1 + 3][0]
                            self.equations.append(expr)

    def func15_angle_bisector_theorem(self):
        triangles = self.logic.find_all_triangles()
        for tri in triangles:
            for z in tri:
                x = tri[1] if z == tri[0] else tri[0]
                y = tri[1] if z == tri[2] else tri[2]
                points = self.logic.find_all_points_on_line((x, y))
                for m in points:
                    if m != x and m != y and self._same(self.logic.find_angle_measure((x, z, m)),
                                                        self.logic.find_angle_measure((y, z, m))):
                        s1, s2, t1, t2 = map(self.logic.find_line_with_length, ((x, z), (y, z), (x, m), (y, m)))
                        # s1 / t1 = s2 / t2
                        expr = s1[0] * t2[0] - t1[0] * s2[0]
                        self.equations.append(expr)

    def func16_cosine_theorem(self):
        triangles = self.logic.find_all_triangles()
        for tri in triangles:
            for _ in permutations(tri):
                angleC, angleB, angleA = [self.logic.find_angle_measure(x) for x in self._generateAngles(_)]
                lines = self._generateLines(_)
                lengthAB, lengthAC, lengthBC = [self.logic.find_line_with_length(x) for x in lines]

                known_edges = sum([hasNumber(x) for x in [lengthAB, lengthAC, lengthBC]])
                if hasNumber(angleC) and (angleC[0] == 90 or known_edges >= 2) \
                        or not hasNumber(angleC) and known_edges == 3:
                    # use sympy.cos/sin to represent number with the variables
                    expr = lengthAC[0] * lengthAC[0] + lengthBC[0] * lengthBC[0] - lengthAB[0] * lengthAB[0] \
                           - 2 * lengthAC[0] * lengthBC[0] * cos(angleC[0] * pi / 180.0)
                    if self._hasSymbol(expr) and (known_edges != 3 or self._isPrimitive(angleC[0])):
                        self.equations.append(expr)

    def func17_sine_theorem(self):
        triangles = self.logic.find_all_triangles()
        for tri in triangles:
            for _ in permutations(tri):
                angleC, angleB, angleA = [self.logic.find_angle_measure(x) for x in self._generateAngles(_)]
                lines = self._generateLines(_)
                lengthAB, lengthAC, lengthBC = [self.logic.find_line_with_length(x) for x in lines]
                if hasNumber(angleA) and hasNumber(angleB):
                    if 90 in [angleA[0], angleB[0]] or any([hasNumber(x) for x in [lengthAC, lengthBC]]):
                        # use math.cos/sin to calculate the specific value
                        sinA = math.sin if isNumber(angleA[0]) else sin
                        sinB = math.sin if isNumber(angleB[0]) else sin
                        expr = sinA(angleA[0] * pi / 180.0) * lengthAC[0] - sinB(angleB[0] * pi / 180.0) * lengthBC[0]
                        if self._hasSymbol(expr):
                            self.equations.append(expr)

    def _getAnswer(self, target):
        """
        Give the target (The format is defined above) and find its answer if possible.
        """
        if target[0] == 'Value':
            if len(target) == 5:
                tried = self.logic.find_arc_measure(target[2:])
                if hasNumber(tried):
                    if target[1] == 'arc_measure':
                        return tried[0]
                    elif target[1] == "arc_length":
                        points = self.logic.find_points_on_circle(target[2])
                        for i in range(len(points)):
                            length = self.logic.find_line_with_length([target[2], points[i]])
                            if hasNumber(length):
                                return 2 * math.pi * length[0] * tried[0] / 360.0
            elif len(target) == 4:
                tried = self.logic.find_angle_measure(target[1:])
                if hasNumber(tried):
                    return tried[0]
            elif len(target) == 3:
                tried = self.logic.find_line_with_length(target[1:])
                if hasNumber(tried):
                    return tried[0]
            elif len(target) == 2:
                try:
                    return float(target[1])
                except:
                    v = Symbol(target[1])
                    try:
                        return float(self.logic.variables[v])
                    except:
                        pass
            return None

        if target[0] == 'Area':
            l = len(target) - 1
            lengthlst = []
            if l == 1:
                points = self.logic.find_points_on_circle(target[1])
                for i in range(len(points)):
                    length = self.logic.find_line_with_length([target[1], points[i]])
                    if hasNumber(length):
                        return math.pi * length[0] * length[0]

            elif l == 3:
                # The area for triangles
                for i in range(1, l + 1):
                    length = self.logic.find_line_with_length([target[i], target[i % l + 1]])
                    if not hasNumber(length): break
                    lengthlst.append(length[0])
                if len(lengthlst) == 3:
                    return heron_triangle_formula(lengthlst[0], lengthlst[1], lengthlst[2])
                for angle in permutations(target[1:]):
                    angle_measure = self.logic.find_angle_measure(angle)
                    if not hasNumber(angle_measure): break
                    lengthAB = self.logic.find_line_with_length([angle[0], angle[1]])
                    lengthAC = self.logic.find_line_with_length([angle[2], angle[1]])
                    if hasNumber(lengthAB) and hasNumber(lengthAC):
                        return angle_area_formula(lengthAB[0], lengthAC[0], angle_measure[0])

            elif l == 4:
                # The area for trapezoid, parallelogram or rectangle. (upper edge + lower edge) / 2 * height
                alledges = target[1:] + target[1:]
                for i in range(1, 5):
                    upper_edge = alledges[i:i + 2]
                    upper_length = self.logic.find_line_with_length(upper_edge)
                    lower_edge = alledges[i + 2:i + 4]
                    lower_length = self.logic.find_line_with_length(lower_edge)
                    if not hasNumber(upper_length) or not hasNumber(lower_length):
                        continue
                    upper_edge_points = self.logic.find_all_points_on_line(upper_edge)
                    lower_edge_points = self.logic.find_all_points_on_line(lower_edge)
                    angles = self.logic.find_all_90_angles()
                    for angle in angles:
                        if angle[1] in upper_edge_points and angle[0] in upper_edge_points:
                            points = self.logic.find_all_points_on_line([angle[1], angle[2]])
                            intersection = set(points) & set(lower_edge_points)
                            if len(intersection) != 1: continue
                            inter = intersection.pop()
                            if (lower_edge[0], inter, angle[1]) in angles or (lower_edge[1], inter, angle[1]) in angles:
                                lengthH = self.logic.find_line_with_length([angle[1], inter])
                                if hasNumber(lengthH):
                                    return (upper_length[0] + lower_length[0]) * lengthH[0] / 2

                # Divide into two triangles
                for i in range(1, 5):
                    A, B, C, D = target[i], target[i % 4 + 1], target[(i + 1) % 4 + 1], target[(i + 2) % 4 + 1]
                    area1 = self._getAnswer(['area', A, B, C])
                    if area1 is None: continue
                    area2 = self._getAnswer(['area', C, D, A])
                    if area2 is not None: return area1 + area2
                    if self._same(self.logic.find_line_with_length([A, B]),
                                  self.logic.find_line_with_length([C, D])) and \
                            self._same(self.logic.find_line_with_length([B, C]),
                                       self.logic.find_line_with_length([D, A])):
                        return area1 * 2
            return None

        if target[0] == 'Perimeter':
            l = len(target) - 1
            ans = 0
            if l == 1:
                points = self.logic.find_points_on_circle(target[1])
                for i in range(len(points)):
                    length = self.logic.find_line_with_length([target[1], points[i]])
                    if hasNumber(length):
                        return 2 * math.pi * length[0]
                return None
            else:
                for i in range(1, l + 1):
                    length = self.logic.find_line_with_length([target[i], target[i % l + 1]])
                    if not hasNumber(length):
                        return None
                    ans += length[0]
            return ans

        if target[0] in ["SinOf", "CosOf", "TanOf", "CotOf", "HalfOf", "SquareOf", "SqrtOf"]:
            try:
                if target[0] == "SinOf": return math.sin(self._getAnswer(target[1]) / 180.0 * math.pi)
                if target[0] == "CosOf": return math.cos(self._getAnswer(target[1]) / 180.0 * math.pi)
                if target[0] == "TanOf": return math.tan(self._getAnswer(target[1]) / 180.0 * math.pi)
                if target[0] == "CotOf": return 1.0 / math.tan(self._getAnswer(target[1]) / 180.0 * math.pi)
                if target[0] == "HalfOf": return self._getAnswer(target[1]) / 2.0
                if target[0] == "SquareOf": return self._getAnswer(target[1]) ** 2
                if target[0] == "SqrtOf": return self._getAnswer(target[1]) ** 0.5
            except:
                return None

        if target[0] in ["RatioOf", "Add", "Mul", "SumOf"]:
            try:
                if target[0] == "RatioOf": return self._getAnswer(target[1]) / self._getAnswer(target[2])
                if target[0] == "Mul": return self._getAnswer(target[1]) * self._getAnswer(target[2])
                if target[0] in ["Add", "SumOf"]: return sum([self._getAnswer(x) for x in target[1:]])
            except:
                return None

    def initSearch(self):
        self.logic.put_equal_into_symbol()
        self.logic.try_delete_unused_points()  # remove no-use points
        self.logic.init_all_uni_lines()  # initialize all the uni-lines (the line do not contain other lines)
        self.logic.find_hidden_polygons(3)  # find all triangles
        self.logic.find_hidden_polygons(4)  # find all quads
        self.logic.find_hidden_polygons(5)  # find all pentagons
        self.logic.expand_angles()  # add the rest (hidden) angles into the graph and give each of them a symbol
        self.logic.set_angle_sum()  # resolve the relation among angles
        self.logic.set_line_sum()  # resolve the relation among lines (e.g, AB+BC = AC)
        self.logic.set_arc_sum()  # resolve the relation among arcs

        if self.logic.debug:
            print(self.logic.find_all_angle_measures())
            print(self.logic.find_all_lines_with_length())
            print(self.logic.fine_all_arc_measures())
        self.can_search = True
        self.hasSolution = False

    def Search(self, target, order_list, round_or_step, upper_bound, enable_low_first):
        """
        This is the main search process.
        Args:
            target[0] = 'Value'
                target[1:] = ['x']: Find the value of variable x.
                target[1:] = ['A', 'B']: Find the length of line AB.
                target[1:] = ['A', 'B', 'C']: Find the measure of angle ABC.
                target[1:] = ['arc_measure', 'O', 'M', 'N']: Find the measure of arc OMN.
                target[1:] = ['arc_length', 'O', 'M', 'N']:  Find the length of arc OMN.
            target[0] = 'Area'
                target[1:] = ['A', 'B', 'C']: Find the area of triangle ABC.
                target[1:] = ['A', 'B', 'C', 'D']: Find the area of quad ABCD.
            target[0] = 'Perimeter'
                target[1:] = ['O']: Find the perimeter of circle O.
                target[1:] = ['A', 'B', 'C']: Find the perimeter of triangle ABC.
                target[1:] = ['A', 'B', 'C', 'D']: Find the perimeter of quad ABCD.
            target[0] = 'SinOf/CosOf/TanOf/CotOf/HalfOf/SquareOf/SqrtOf/RatioOf/Add/Mul/SumOf"'
                target[1:] = new_target
                For example, [SinOf, [value, 'A', 'B', 'C']] or [Add, ['value', 'A', 'B'], ['value', 'C', 'D']]
        Returns:
            (float) The value of the target.

        Note: if the goal is to find 'sin \\angle ABC', use this function to calc 'value ABC'
            and finally do the sine outside this function.
        """

        if target is None:
            return None
        assert self.can_search, "Please execute initSearch() before search."

        # try to get the answer before using theorems
        step_lst = []
        now_answer = self._getAnswer(target)
        if now_answer is not None:
            return now_answer, 0, step_lst

        if round_or_step:
            rounds = 0
            Update = True
            while rounds <= upper_bound and Update:
                rounds += 1
                Update = False
                self.equations = []
                for i in range(1, len(self.function_maps)+1):
                    if enable_low_first and i > self.interval: continue
                    step_lst.append(i)
                    changed = self.function_maps[i]()
                    if changed is not None and changed:
                        Update = True
                Update = Update or len(self.equations) > 0
                FindSolution = self.Solve_Equations()
                now_answer = self._getAnswer(target)
                if now_answer is not None:
                    return now_answer, rounds, step_lst
                if not enable_low_first or FindSolution: continue
                self.equations = []
                for i in range(self.interval+1, len(self.function_maps)+1):
                    step_lst.append(i)
                    self.function_maps[i]()
                Update = Update or len(self.equations) > 0
                self.Solve_Equations()
                now_answer = self._getAnswer(target)
                if now_answer is not None:
                    return now_answer, rounds, step_lst

            self.Solve_Equations()
            now_answer = self._getAnswer(target)
            if now_answer is not None:
                return now_answer, rounds, step_lst
            return None, rounds, step_lst

        else:
            # check order_lst
            func_ids = self.function_maps.keys()
            if isinstance(order_list, list) and len(order_list) > 0:
                result = all([order in func_ids for order in order_list])
                if not result:
                    order_list = []
            else:
                order_list = []

            # Run the predicting series.
            steps = 0
            for element in order_list:
                steps += 1
                step_lst.append(element)
                self.equations = []
                self.function_maps[element]()
                self.Solve_Equations()
                now_answer = self._getAnswer(target)
                if now_answer is not None:
                    return now_answer, steps, step_lst

            Update = True
            while Update and steps < upper_bound:
                # print (self.logic.find_all_angle_measures())
                # print (self.logic.find_all_lines_with_length())
                # print (self.logic.variables)
                Update = False
                FindSolution = False
                for i in range(1, len(self.function_maps)+1):
                    if enable_low_first and i > self.interval:
                        continue
                    steps += 1
                    step_lst.append(i)
                    self.equations = []
                    changed = self.function_maps[i]()
                    if changed is not None and not changed or changed is None and len(self.equations) == 0:
                        continue
                    Update = True
                    FindSolution = self.Solve_Equations() or FindSolution
                    now_answer = self._getAnswer(target)
                    if now_answer is not None:
                        return now_answer, steps, step_lst

                if not enable_low_first or FindSolution: continue
                for i in range(self.interval+1, len(self.function_maps)+1):
                    steps += 1
                    step_lst.append(i)
                    self.equations = []
                    self.function_maps[i]()
                    if len(self.equations) == 0: continue
                    Update = True
                    self.Solve_Equations()
                    now_answer = self._getAnswer(target)
                    if now_answer is not None:
                        return now_answer, steps, step_lst

                self.Solve_Equations()

            now_answer = self._getAnswer(target)
            if now_answer is not None:
                return now_answer, steps, step_lst
            return None, steps, step_lst

    def reflex_angle(self, points):  # find all the reflex angles in a polygon
        p = [self.logic.point_positions[x] for x in points]
        p.sort(key=lambda x: (x[0], x[1]))
        cross = lambda p, q, r: (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        lower = []
        for x in p:
            while len(lower) > 1 and cross(lower[-2], lower[-1], x) <= 0:
                lower.pop()
            lower.append(x)
        upper = []
        for x in reversed(p):
            while len(upper) > 1 and cross(upper[-2], upper[-1], x) <= 0:
                upper.pop()
            upper.append(x)
        convex_hull = lower[:-1] + upper[:-1]
        concave_hull = [p[i] for i in range(len(p)) if p[i] not in convex_hull]
        res = []
        for i in range(0, len(concave_hull)):
            res += list(self.logic.point_positions.keys())[list(self.logic.point_positions.values()).index(concave_hull[i])]
        return res