import functools
import algopy
# import pyipopt
from scipy.optimize import minimize, newton_krylov, basinhopping
import numpy as np
from scipy.optimize.nonlin import NoConvergence
import time

from geosolver.ontology.ontology_semantics import evaluate, TruthValue
from geosolver.solver.variable_handler import VariableHandler
from geosolver.ontology.ontology_definitions import FormulaNode

__author__ = 'minjoon'


class NumericSolver(object):
    def __init__(self, prior_atoms, variable_handler=None, max_num_resets=3, tol=10**-3, assignment=None):
        if variable_handler is None:
            variable_handler = VariableHandler()
        self.variable_handler = variable_handler
        self.atoms = [variable_handler.add(prior_atom, assignment=assignment) for prior_atom in prior_atoms]
        self.max_num_resets = max_num_resets
        self.tol = tol
        self.assignment = None
        self.assigned = False
        self.confidence = None

    def solve(self):
        self.assignment, self.confidence = find_assignment(self.variable_handler, self.atoms, self.max_num_resets, self.tol)
        self.assigned = True

    def is_sat(self, th=None):
        if th is None:
            th = self.tol
        if not self.assigned:
            self.solve()
        return self.confidence < th

    def query_invar(self, query_atom, th=None):
        query_atom = self.variable_handler.add(query_atom)
        if self.is_sat(th):
            return evaluate(query_atom, self.assignment).norm < self.tol
        else:
            return False

    def find_assignment(self, query_atom):
        query_atom = self.variable_handler.add(query_atom)
        return find_assignment(self.variable_handler, self.atoms + [query_atom], self.max_num_resets, self.tol)

    def evaluate(self, variable_node, th=None):
        variable_node = self.variable_handler.add(variable_node)
        if not self.assigned:
            self.solve()
        return evaluate(variable_node, self.assignment)


def find_assignment(variable_handler, atoms, max_num_resets, tol, verbose=True):
    init = variable_handler.dict_to_vector()

    def func(vector):
        return sum(evaluate(atom, variable_handler.vector_to_dict(vector)).norm for atom in atoms)

    xs = []
    fs = []
    options = {'ftol': tol**2}
    minimizer_kwargs = {"method": "SLSQP", "options": options}
    for i in range(max_num_resets):
        result = basinhopping(func, init, minimizer_kwargs=minimizer_kwargs)
        if verbose:
            print("iteration %d:" % (i+1))
            print(result)
        xs.append(result.x)
        fs.append(result.fun)
        if result.fun < tol:
            break
        init = np.random.rand(len(init))

    min_idx = min(enumerate(fs), key=lambda pair: pair[1])[0]
    assignment = variable_handler.vector_to_dict(xs[min_idx])
    norm = fs[min_idx]
    return assignment, norm

def _find_assignment(variable_handler, atoms, max_num_resets, tol, verbose=False):
    init = np.array(variable_handler.dict_to_vector())

    def func(vector):
        print ("dim:", np.shape(vector), vector)
        d = variable_handler.vector_to_dict(vector)
        return sum(evaluate(atom, d).norm for atom in atoms)

    def grad(f, theta):
        theta = algopy.UTPM.init_jacobian(theta)
        return algopy.UTPM.extract_jacobian(f(theta))

    def hess(f, theta):
        theta = algopy.UTPM.init_hessian(theta)
        return algopy.UTPM.extract_hessian(len(theta), f(theta))

    x = None
    for i in range(max_num_resets):
        results = pyipopt.fmin_unconstrained(func, init, functools.partial(grad, func))
        if verbose:
            print("iteration %d:" % (i+1))
            print(results)
        val, zl, zu, constraint_multipliers, obj, status = results
        if obj < tol:
            x = val
            break
        init = np.random.rand(len(init))

    if x is None:
        return None
    return variable_handler.vector_to_dict(x)
