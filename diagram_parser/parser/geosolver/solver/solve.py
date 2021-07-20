import logging
import time
from geosolver.ontology.ontology_semantics import evaluate, Equals
from geosolver.solver.display_entities import display_entities
from geosolver.solver.numeric_solver import NumericSolver
from geosolver.ontology.ontology_definitions import FormulaNode, signatures

__author__ = 'minjoon'

def solve(given_formulas, choice_formulas=None, assignment=None):
    """

    :param list true_formulas:
    :param dict choice_formulas:
    :return:
    """
    start_time = time.time()
    out = {}
    #1. Find query formula in true formulas
    true_formulas = []
    query_formula = None
    for formula in given_formulas:
        assert isinstance(formula, FormulaNode)
        if formula.has_signature("What") or formula.has_signature("Which") or formula.has_signature("Find"):
            if query_formula is not None:
                logging.warning("More than one query formula.")
            query_formula = formula
        else:
            true_formulas.append(formula)
    if query_formula is None:
        raise Exception("No query formula.")

    elif query_formula.has_signature("What"):
        if choice_formulas is None:
            ns = NumericSolver(given_formulas, assignment=assignment)
            ns.solve()
            out = ns.assignment['What']
        else:
            ns = NumericSolver(given_formulas, assignment=assignment)
            ns.solve()
            for key, choice_formula in choice_formulas.iteritems():
                equal_formula = FormulaNode(signatures['Equals'], [ns.assignment['What'], choice_formula])
                out[key] = ns.evaluate(equal_formula)

            """
            ns = NumericSolver(true_formulas)
            ns.solve()
            for key, choice_formula in choice_formulas.iteritems():
                # print query_formula.children[1], ns.evaluate(query_formula.children[1])
                # print choice_formula, ns.evaluate(choice_formula)
                tester = lambda node: isinstance(node, FormulaNode) and node.signature.id == "What"
                getter = lambda node: choice_formula
                replaced_formula = query_formula.replace_node(tester, getter)
                # print replaced_formula
                out[key] = ns.evaluate(replaced_formula)
            """
        # display_entities(ns)

    elif query_formula.has_signature("Find"):
        ns = NumericSolver(true_formulas, assignment=assignment)
        ns.solve()
        # display_entities(ns)
        if choice_formulas is None:
            # No choice given; need to find the answer!
            out = ns.evaluate(query_formula.children[0])
        else:
            for key, choice_formula in choice_formulas.iteritems():
                replaced_formula = FormulaNode(signatures['Equals'], [query_formula.children[0], choice_formula])
                out[key] = ns.evaluate(replaced_formula)
        # display_entities(ns)


    elif query_formula.has_signature("Which"):
        ns = NumericSolver(true_formulas, assignment=assignment)
        ns.solve()
        for key, choice_formula in choice_formulas.iteritems():
            # print query_formula.children[1], ns.evaluate(query_formula.children[1])
            # print choice_formula, ns.evaluate(choice_formula)
            tester = lambda node: node.signature.id == "Which"
            getter = lambda node: choice_formula
            replaced_formula = query_formula.replace_node(tester, getter)
            out[key] = ns.evaluate(replaced_formula)

    # this won't be executed!
    elif query_formula.has_signature("Which"):
        tester = lambda node: isinstance(node, FormulaNode) and node.signature.id == "Which"
        for choice, choice_formula in choice_formulas.iteritems():
            getter = lambda node: choice_formula
            replaced_formula = query_formula.replace_node(tester, getter)
            all_formulas = true_formulas + [replaced_formula]
            ns = NumericSolver(all_formulas)
            out[choice] = ns.evaluate(replaced_formula)
            print (out[choice])

            #display_entities(ns)
    else:
        raise Exception()

    end_time = time.time()
    delta_time = end_time - start_time
    print ("%.2f seconds" % delta_time)
    return out