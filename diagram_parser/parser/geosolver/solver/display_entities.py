import matplotlib.pyplot as plt

from geosolver.solver.numeric_solver import NumericSolver
from geosolver.ontology.ontology_definitions import FormulaNode

__author__ = 'minjoon'


def display_entities(numeric_solver):
    assert isinstance(numeric_solver, NumericSolver)
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    for name, entity in numeric_solver.variable_handler.named_entities.iteritems():
        assert isinstance(entity, FormulaNode)
        type_ = entity.signature.id
        grounded_entity = numeric_solver.evaluate(entity)
        if type_ == "Point":
            x, y = grounded_entity
            ax.plot(x, y, 'ro')
            ax.text(x, y, name)
    plt.show()
