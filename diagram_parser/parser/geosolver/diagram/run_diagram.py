import os

import cv2

from geosolver import geoserver_interface
from geosolver.diagram.computational_geometry import normalize_angle, horizontal_angle, area_of_polygon
from geosolver.diagram.get_instances import get_all_instances
from geosolver.diagram.parse_confident_formulas import parse_confident_formulas
from geosolver.diagram.parse_core import parse_core
from geosolver.diagram.parse_graph import parse_graph
from geosolver.diagram.parse_image_segments import parse_image_segments
from geosolver.diagram.parse_primitives import parse_primitives
from geosolver.diagram.select_primitives import select_primitives
from geosolver.utils.prep import open_image
import numpy as np

__author__ = 'minjoon'

def test_parse_image_segments():
    question = geoserver_interface.download_questions(1037).values()[0]
    image_segment_parse = parse_image_segments(open_image(question.diagram_path))
    image_segment_parse.diagram_image_segment.display_binarized_segmented_image()
    for idx, label_image_segment in image_segment_parse.label_image_segments.iteritems():
        label_image_segment.display_segmented_image()


def save_parse_image_segments():
    question = geoserver_interface.download_questions(1037).values()[0]
    image_segment_parse = parse_image_segments(open_image(question.diagram_path))
    image = image_segment_parse.diagram_image_segment.segmented_image
    file_path = "/Users/minjoon/Desktop/diagram.png"
    cv2.imwrite(file_path, image)


def test_parse_primitives():
    question = geoserver_interface.download_questions(1037).values()[0]
    image_segment_parse = parse_image_segments(open_image(question.diagram_path))
    primitive_parse = parse_primitives(image_segment_parse)
    primitive_parse.display_primitives()


def save_parse_primitives():
    question = geoserver_interface.download_questions(1037).values()[0]
    image_segment_parse = parse_image_segments(open_image(question.diagram_path))
    primitive_parse = parse_primitives(image_segment_parse)
    image = primitive_parse.get_image_primitives()
    file_path = "/Users/minjoon/Desktop/primitives.png"
    cv2.imwrite(file_path, image)


def test_select_primitives():
    question_dict = geoserver_interface.download_questions(1037)
    for key in sorted(question_dict.keys()):
        question = question_dict[key]
        print(key)
        image_segment_parse = parse_image_segments(open_image(question.diagram_path))
        primitive_parse = parse_primitives(image_segment_parse)
        selected = select_primitives(primitive_parse)
        selected.display_primitives()


def save_select_primitives():
    question_dict = geoserver_interface.download_questions('test')
    folder_path = "/Users/minjoon/Desktop/selected/"
    for key in sorted(question_dict.keys()):
        question = question_dict[key]
        print(key)
        image_segment_parse = parse_image_segments(open_image(question.diagram_path))
        primitive_parse = parse_primitives(image_segment_parse)
        selected = select_primitives(primitive_parse)
        image = selected.get_image_primitives()
        cv2.imwrite(os.path.join(folder_path, "%s.png" % str(question.key)), image)


def test_parse_core():
    question_dict = geoserver_interface.download_questions(1037)
    for key in sorted(question_dict.keys()):
        question = question_dict[key]
        print(key)
        image_segment_parse = parse_image_segments(open_image(question.diagram_path))
        primitive_parse = parse_primitives(image_segment_parse)
        selected = select_primitives(primitive_parse)
        core_parse = parse_core(selected)
        core_parse.display_points()


def save_parse_core():
    question_dict = geoserver_interface.download_questions('test')
    folder_path = "/Users/minjoon/Desktop/core/"
    for key in sorted(question_dict.keys()):
        print(key)
        question = question_dict[key]
        file_path = os.path.join(folder_path, str(question.key) + ".png")
        if os.path.isfile(file_path):
            continue
        image_segment_parse = parse_image_segments(open_image(question.diagram_path))
        primitive_parse = parse_primitives(image_segment_parse)
        selected = select_primitives(primitive_parse)
        core_parse = parse_core(selected)
        image = core_parse.get_image_points()
        cv2.imwrite(file_path, image)


def test_parse_graph():
    questions = geoserver_interface.download_questions(973).values()
    for question in questions:
        image_segment_parse = parse_image_segments(open_image(question.diagram_path))
        primitive_parse = parse_primitives(image_segment_parse)
        selected_primitive_parse = select_primitives(primitive_parse)
        core_parse = parse_core(selected_primitive_parse)
        graph_parse = parse_graph(core_parse)

        print("Confident information in the diagram:")
        for variable_node in parse_confident_formulas(graph_parse):
            print variable_node

        core_parse.display_points()
        lines = get_all_instances(graph_parse, 'line')
        circles = get_all_instances(graph_parse, 'circle')
        arcs = get_all_instances(graph_parse, 'arc')
        angles = get_all_instances(graph_parse, 'angle')
        print("Displaying lines...")
        for key, line in lines.iteritems():
            graph_parse.display_instances([line])
        print("Displaying circles...")
        for key, circle in circles.iteritems():
            graph_parse.display_instances([circle])
        print("Displaying arcs...")
        for key, arc in arcs.iteritems():
            graph_parse.display_instances([arc])
        print("Displaying angles...")
        for key, angle in angles.iteritems():
            graph_parse.display_instances([angle])

def test_computational_geometry():
    ans = area_of_polygon([(0,0), (1,0), (1,1), (0,1)])
    print ans


if __name__ == "__main__":
    # test_parse_image_segments()
    # save_parse_image_segments()
    # test_parse_primitives()
    # save_parse_primitives()
    # test_select_primitives()
    # save_select_primitives()
    test_parse_core()
    # save_parse_core()
    # test_parse_graph()
    # test_computational_geometry()
