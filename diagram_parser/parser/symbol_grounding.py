import copy
from geosolver.diagram.states import GraphParse
from geosolver.diagram.get_instances import get_all_instances
from geosolver.grounding.label_distances import label_distance_to_line, label_distance_to_point, \
                                                label_distance_to_arc,label_distance_to_angle
from geosolver.ontology.ontology_definitions import *
from geosolver.ontology.ontology_semantics import *

def parser_to_generate_description(graph_parse, known_labels, delete_points, formula_list, log_message):
    assert isinstance(graph_parse, GraphParse)
    
    circles = graph_parse.circle_dict
    points = {}
    for idx, pos in get_all_instances(graph_parse, "point").items():
        if not idx in delete_points or idx in circles.keys():
            points[idx] = pos
    point_key_dict = {}
    offset = graph_parse.image_segment_parse.diagram_image_segment.offset
    known_labels = copy.deepcopy(known_labels)
    
    
    if len(circles) > 0:
        for center in circles.keys():
            distances = [(label, label_distance_to_point(points[center], instantiators['point'](label['x'], label['y']))) \
                           for label in known_labels if label['type'] == 'point']
            if len(distances) > 0:
                # We should find a nearby label as the center of circlce.
                # print (distances)
                v = min(distances, key=lambda pair: pair[1])
                if v[1] > 35: continue
                label = v[0]
                known_labels.remove(label)
                formula = graph_parse.point_variables[center]
                formula_list.append(formula)
                point_key_dict[label['label']] = center

    for idx, d in enumerate(known_labels):
        type_, label = d['type'],  d['label']
        x, y = d['x'], d['y']
        arr = type_.split(' ')
        label_point = instantiators['point'](x, y)
        if len(arr) > 1:
            type_ = arr[-1]
        
        instances = {}
        for idx, pos in get_all_instances(graph_parse, type_).items():
            if type(idx) == int:
                if not idx in delete_points:
                    instances[idx] = pos
            else:
                if len(set(idx) & set(delete_points)) == 0:
                    instances[idx] = pos 
        
        if len(arr) > 1 and type_ == 'line' and arr[0] == 'length':
            distances = [(key, label_distance_to_line(label_point, instance, True)) for key, instance in instances.items()]
        elif type_ == 'line':
            distances = [(key, label_distance_to_line(label_point, instance, False)) for key, instance in instances.items()]
        elif type_ == 'point':
            #print (x, y, label)
            distances = [(key, label_distance_to_point(label_point, instance)) for key, instance in instances.items() if not key in circles.keys()]
        elif type_ == 'arc':
            distances = [(key, label_distance_to_arc(label_point, instance)) for key, instance in instances.items()]
        elif type_ == 'angle':
            # filter subangles
            distances = [(key, label_distance_to_angle(label_point, instance)) for key, instance in instances.items()]
        
        #print (type_, label, distances)
        if len(distances) == 0: 
            log_message.append('The distances is empty, but there is: ' + str(label) + ' ' + str(type_))
            continue
        argmin_key = min(distances, key=lambda pair: pair[1])[0]
        
        if type_ == 'line':
            a_key, b_key = argmin_key
            a_point = graph_parse.point_variables[a_key]
            b_point = graph_parse.point_variables[b_key]
            # print (a_key, b_key, a_point, b_point, label)
            formula = FormulaNode(signatures['Line'], [a_point, b_point])
            formula = FormulaNode(signatures['LengthOf'], [formula])
            
            label = label.lower()
            if len(arr) > 1 and arr[0] == 'length':
                label_formula = FormulaNode(Signature(label, 'number'), [])
                formula = FormulaNode(signatures['Equals'], [formula, label_formula])
            else:
                label_formula = FormulaNode(VariableSignature(label, 'line'), [])
                formula = FormulaNode(signatures['Equals'], [formula, label_formula])
                
        elif type_ == 'point':
            #print (distances, argmin_key)
            formula = graph_parse.point_variables[argmin_key]
            point_key_dict[label] = argmin_key
        elif type_ == 'angle':
            a_key, b_key, c_key = argmin_key
            a_point = graph_parse.point_variables[a_key]
            b_point = graph_parse.point_variables[b_key]
            c_point = graph_parse.point_variables[c_key]
            formula = FormulaNode(signatures['Angle'], [a_point, b_point, c_point])
            formula = FormulaNode(signatures['MeasureOf'], [formula])
            label = label.lower()
            if len(arr) > 1 and arr[0] == 'angle': 
                label_formula = FormulaNode(Signature(label, 'number'), [])
                formula = FormulaNode(signatures['Equals'], [formula, label_formula])
            else:
                label_formula = FormulaNode(VariableSignature("angle " + label, 'angle'), [])
                formula = FormulaNode(signatures['Equals'], [formula, FormulaNode(signatures['MeasureOf'], [label_formula])])
        formula_list.append(formula)
    return point_key_dict
