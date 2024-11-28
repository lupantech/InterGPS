import os
import sys
import cv2
import json
from tqdm import tqdm
import argparse
from multiprocess import Pool
import matplotlib.pyplot as plt

from geosolver.diagram.parse_confident_formulas import parse_confident_formulas
from geosolver.diagram.get_instances import get_all_instances
from geosolver.ontology.ontology_definitions import *

from load_symbol import load_symbol
from use_geosolver import image_to_graph_parse
from parse_symbol import generate_label
from symbol_grounding import parser_to_generate_description
from generate_logic_form import solveSigns, solvePerpendicular, solveParallels, solveLines, solveAngles


def multithread_solve(parameters):
    # Unpack parameters
    data_id, box_id, ocr_result, sign_result, data, img, factor = parameters
    
    log_message = []
    
    graph_parse = image_to_graph_parse(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    points = get_all_instances(graph_parse, 'point')
    
    '''Generate logic forms about signs'''
    delete_points, formula_list = solveSigns(graph_parse, factor, sign_result, log_message)
    known_label = generate_label(graph_parse, ocr_result, delete_points, factor, log_message)

    '''Generate label data and add basic logic forms in the diagram.'''
    
    point_key_dict = parser_to_generate_description(graph_parse, known_label, delete_points, formula_list, log_message)
    
    '''Add logic forms about PointLieOnLine and PointLieOnCircle.'''
    for variable_node in parse_confident_formulas(graph_parse):
        result = variable_node.simple_repr()
        # We need to get rid of some illegal points.
        legal = True
        import re
        #print (re.split(',\(\)', result))
        for element in re.split(r'[,\(\)]', result):
            try:
                val = int(element.replace('point_', ''))
                if val in delete_points:
                    legal = False
            except:
                pass
        if legal:
            formula_list.append(variable_node)
    
    '''
    Assign remain letters to the points.
    Also replace each point with the corresponding letter in logic forms.
    '''
    points = get_all_instances(graph_parse, 'point')
    used = [False] * 26
    replace = {}
    for label, number in point_key_dict.items():
        if label.isupper():
            used[ord(label)-65] = True
        replace['point_' + str(number)] = label
    for number in points.keys():
        if not number in delete_points and not ('point_' + str(number)) in replace:
            try:
                id = used.index(False)
                used[id] = True
                replace['point_' + str(number)] = chr(id+65)
            except:
                log_message.append("The letter is used up...")
                break

    '''Generate logic forms in string format.'''
    new_formula_list = []
    logic_forms = []
    for formula in formula_list:
        if formula.is_leaf(): continue
        tester = lambda x: x.simple_repr() in replace
        gester = lambda x: FormulaNode(Signature(replace[x.simple_repr()], 'point'), [])

        new_formula = formula.replace_signature(tester, gester)
        new_formula_list.append(new_formula)
        # print (new_formula.simple_repr())
        logic_forms.append(new_formula.simple_repr())
    
    answer = {}
    answer["id"] = data_id
    answer["log"] = log_message
    answer['point_instances'] = [replace.get('point_' + str(ch), 'point_' + str(ch)) 
                                          for ch in get_all_instances(graph_parse, 'point').keys()]
    answer['line_instances'] = [replace.get('point_' + str(ch[0]), 'point_' + str(ch[0])) +
                                         replace.get('point_' + str(ch[1]), 'point_' + str(ch[1])) 
                                         for ch in get_all_instances(graph_parse, 'line').keys()]
    answer['circle_instances'] = [replace.get('point_' + str(center), 'point_' + str(center)) 
                                           for center in graph_parse.circle_dict.keys()]
    answer['diagram_logic_forms'] = logic_forms
    answer['point_positions'] = {replace.get('point_' + str(ch)): (value.x, value.y) 
                                          for ch, value in points.items()}

    
    return answer

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Main program for diagram parsing')

    parser.add_argument('--data_path', default='../../data/geometry3k')
    parser.add_argument('--ocr_path', default='../detection_results/ocr_results')
    parser.add_argument('--box_path', default='../detection_results/box_results')
    parser.add_argument('--output_path', default='diagram_logic_form.json')
    
    parser = parser.parse_args()

    # mapping_file = 'number_index.json'
    # log_file = 'log' + time.time() + ".txt"
    # print (log_file)

    # with open(mapping_file) as f:
    #     from_id_to_newid = json.load(f)
        
    test_data = list(range(2401, 3002))
    detection_id = list(map(str, test_data))

    ocr_results, sign_results, size_results = load_symbol(detection_id, parser.ocr_path, parser.box_path)
    
    para_lst = []
    for data_id in test_data:
        box_id = str(data_id)
        input_path = os.path.join(parser.data_path, "test", str(data_id))
        json_file = os.path.join(input_path, "data.json")
        with open(json_file, 'r') as f:
            data = json.load(f)
        diagram_path = os.path.join(input_path, "img_diagram.png")
        img = cv2.imread(diagram_path)
        factor = (1, 1)
        if size_results[box_id] is not None:
            factor = (img.shape[1] / size_results[box_id][1], img.shape[0] / size_results[box_id][0])
        para_lst.append((data_id, box_id, ocr_results[box_id], sign_results[box_id], data, img, factor))
    
    solve_list = []
    with tqdm(total=len(para_lst), ncols=80) as t:
        with Pool(10) as p:
            for answer in p.imap_unordered(multithread_solve, para_lst):
                solve_list.append(answer)
                t.update()
    
    
    solve_list = sorted(solve_list, key=lambda x: int(x['id']))
    final = {}
    for entry in solve_list:
        id = entry["id"]
        del entry["id"]
        final[id] = entry
    with open(parser.output_path, "w") as f:
        json.dump(final, f, indent = 2)
        
        