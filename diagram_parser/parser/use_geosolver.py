from geosolver.diagram.parse_core import parse_core
from geosolver.diagram.parse_graph import parse_graph
from geosolver.diagram.parse_image_segments import parse_image_segments
from geosolver.diagram.parse_primitives import parse_primitives
from geosolver.diagram.select_primitives import select_primitives

def image_to_graph_parse(diagram):
    '''Parse the diagram using GeoSolver.'''
    image_segment_parse = parse_image_segments(diagram)
    primitive_parse = parse_primitives(image_segment_parse)
    selected_primitive_parse = select_primitives(primitive_parse)
    core_parse = parse_core(selected_primitive_parse)
    graph_parse = parse_graph(core_parse)
    return graph_parse