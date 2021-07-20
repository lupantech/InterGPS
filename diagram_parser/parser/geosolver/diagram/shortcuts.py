from geosolver.diagram.parse_core import parse_core
from geosolver.diagram.parse_graph import parse_graph
from geosolver.diagram.parse_image_segments import parse_image_segments
from geosolver.diagram.parse_primitives import parse_primitives
from geosolver.diagram.select_primitives import select_primitives
from geosolver.grounding.parse_match_from_known_labels import parse_match_from_known_labels
from geosolver.utils.prep import open_image

__author__ = 'minjoon'


def question_to_graph_parse(question):
    diagram = open_image(question.diagram_path)
    image_segment_parse = parse_image_segments(diagram)
    primitive_parse = parse_primitives(image_segment_parse)
    selected_primitive_parse = select_primitives(primitive_parse)
    core_parse = parse_core(selected_primitive_parse)
    graph_parse = parse_graph(core_parse)
    return graph_parse

def question_to_match_parse(question, label_data):
    graph_parse = question_to_graph_parse(question)
    match_parse = parse_match_from_known_labels(graph_parse, label_data)
    return match_parse

def questions_to_match_parses(questions, labels):
    match_parses = {}
    for key, question in questions.iteritems():
        print (key)
        label = labels[key]
        match_parse = question_to_match_parse(question, label)
        match_parses[key] = match_parse
    return match_parses

