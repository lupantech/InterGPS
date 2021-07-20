from geosolver.diagram.get_instances import get_all_instances
from geosolver.diagram.computational_geometry import distance_between_points, distance_between_line_and_point
from geosolver.grounding.label_distances import label_distance_to_line, label_distance_to_point
from geosolver.ontology.ontology_definitions import *
from geosolver.ontology.ontology_semantics import *

def count_numbers(ocr_result):
    numbers = {}
    for result in ocr_result:
        try:
            label = int(result[4])
            numbers[label] = numbers.get(label, 0) + 1
        except:
            pass
    return numbers

def seem_angle(numbers, label, point_distances, line_distances):
    '''A single number can also represent an angle, and we try to figure it out.'''
    count = 1
    while count in numbers:
        count += 1
    try:
        num = int(label)
        series = 1
        for i in range(1, 4):
            if not num + i in numbers: break
            series += 1
        for i in range(1, 4):
            if not num - i in numbers: break
            series += 1
        # print (num, series, count, label)
        if 2 * min(line_distances) >= min(point_distances) or numbers[num] == 1:
            if count > 2 and num < count: return True
            if series >= 4: return True
            if series >= 2 and 1.5 * min(line_distances) >= min(point_distances): return True
        return False
    except:
        return False

def generate_label(graph_parse, ocr_result, delete_points, factor, log_message):
    points = {}
    for idx, pos in get_all_instances(graph_parse, "point").items():
        if not idx in delete_points:
            points[idx] = pos
    lines = {}
    for idx, pos in get_all_instances(graph_parse, "line").items():
        if len(set(idx) & set(delete_points)) == 0:
            lines[idx] = pos
    offset = graph_parse.image_segment_parse.diagram_image_segment.offset
    numbers = count_numbers(ocr_result)
    label_result = []
    
    for element in ocr_result:
        label = element[4]
        position = instantiators['point']((element[0] + element[2]) / 2 * factor[0] - offset[0], 
                                        (element[1] + element[3]) / 2 * factor[1] - offset[1])
        #print ("!!", element, factor, position, label)
        structure = {"x": position.x, "y": position.y, "label": label, "type": ""}
        point_distances = [label_distance_to_point(position, instance) for key, instance in points.items()]
        line_distances = [min(distance_between_line_and_point(instance, position), label_distance_to_line(position, instance, True))
                              for key, instance in lines.items()]
        
        if "^{\circ}" in label:
            structure['type'] = 'angle angle'
            structure['label'] = label[0: label.find("^{\circ}")]
        elif len(label) == 1 and label.isalpha():
            alpha = 1
            if len(line_distances) > 0 and len(point_distances) > 0:
                alpha = min(point_distances) / min(line_distances)
                # print (alpha, label)
            if alpha >= 3 or alpha >= 1.8 and label in ['X', 'Z']:
                # Point X may recognize as length x, so we should assure that x is closer to the line.
                label = label.lower()
            if label.islower():
                structure['type'] = 'length line'
                structure['label'] = label
                # Basically, using 'x/y/z' to represent the length of a line is different from using 'l/m/n' to represent a line.
                # In this code, we consider them as the same thing.
            else:
                structure['type'] = 'point'
                structure['label'] = label
        elif any([str(ch) in label for ch in range(10)]):
            structure['type'] = 'length line'
            if seem_angle(numbers, label, point_distances, line_distances):
                structure['type'] = 'angle'
        if structure["type"] == "":
            log_message.append(str(label) + " can not be recognized.")
        else:
            label_result.append(structure)
    return label_result