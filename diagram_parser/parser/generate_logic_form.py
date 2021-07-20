'''
This block is to detect signs and generate the corresponding logic forms.
It is the most important part for our new diagram parser.
'''

import math

from geosolver.ontology.ontology_definitions import *
from geosolver.ontology.ontology_semantics import *
from geosolver.diagram.get_instances import get_all_instances

def dist(a, b):
    return sum([(int(pa[0]) - int(pa[1]))**2 for pa in zip(a, b)]) ** 0.5

def calc_angle(p0, p1, p2):
    clen = lambda x: (x[0] ** 2 + x[1] ** 2) ** 0.5
    q0 = (p0[0] - p1[0], p0[1] - p1[1])
    q2 = (p2[0] - p1[0], p2[1] - p1[1])
    costheta = (q0[0] * q2[0] + q0[1] * q2[1]) / clen(q0) / clen(q2)
    costheta = min(costheta, 1.0)
    costheta = max(costheta, -1.0)
    return math.acos(costheta)

def cross(p0, p1, p2):
    return (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p2[0] - p0[0]) * (p1[1] - p0[1])

def in_box(point, box, gap = 0):
    return point[0] >= box[0]-gap and point[0] <= box[2]+gap and point[1] >= box[1]-gap and point[1] <= box[3]+gap

def in_line(line, point):
    # (line.a - point) * (line.b - point) <= 0
    # print (line, point, (line.a.x - point.x) * (line.b.x - point.x) + (line.b.y - point.y) * (line.a.y - point.y))
    return ((line[0][0] - point[0]) * (line[1][0] - point[0]) + (line[1][1] - point[1]) * (line[0][1] - point[1]) <= 0
            or dist(line[0], point) <= 4 or dist(line[1], point) <= 4)

def solvePerpendicular(box, graph_parse, delete_points, formula_list, log_message):
    points = get_all_instances(graph_parse, 'point')
    angles = get_all_instances(graph_parse, 'angle')
    choose, maxlen = None, 0.0
    for idx, pos in angles.items():
        if len(set(idx) & set(delete_points)) > 0: continue
        angle = calc_angle(pos[0], pos[1], pos[2])
        if in_box(pos[1], box, gap = 5):   # change 3 to 5
            # The angle needs to approach pi/2 (90).
            if angle >= math.pi / 2.0 - 0.15 and angle <= math.pi / 2.0 + 0.15:
                # Try to find out one of those angles with maximum length.
                nowlen = dist(pos[0], pos[1]) + dist(pos[2], pos[1])
                if nowlen > maxlen:
                    maxlen, choose = nowlen, idx
    if choose == None:
        log_message.append("Can not find the corresponding right angle:" + str(box))
        return
    for idx, pos in points.items():
        if not idx in choose and in_box(pos, box):
            delete_points.append(idx)
    choose = [graph_parse.point_variables[x] for x in choose]
    line0 = FormulaNode(signatures['Line'], [choose[1], choose[0]])
    line1 = FormulaNode(signatures['Line'], [choose[1], choose[2]])
    formula_list.append(FormulaNode(signatures['Perpendicular'], [line0, line1]))

def solveParallels(boxes, graph_parse, delete_points, formula_list, log_message):
    points = get_all_instances(graph_parse, 'point')
    lines = get_all_instances(graph_parse, 'line')
    lists = []
    for box in boxes:
        mid = ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)
        choose, maxlen = None, 0.0
        for idx, pos in lines.items():
            if len(set(idx) & set(delete_points)) > 0: continue
            angle = calc_angle(pos[0], mid, pos[1])
            # The angle needs to approach pi (180).
            if angle >= math.pi - 0.2:
                # Assume that the midpoint of the box lies on the current line.
                nowlen = dist(pos[0], mid) + dist(pos[1], mid)
                if nowlen > maxlen:
                    maxlen, choose = nowlen, idx
        if choose == None:
            log_message.append ("Can not find the corresponding parallel lines:" + str(box))
        else:
            for idx, pos in points.items():
                if not idx in choose and in_box(pos, box):
                    delete_points.append(idx)
            choose = [graph_parse.point_variables[x] for x in choose]
            assert len(choose) == 2
            lists.append(FormulaNode(signatures['Line'], choose))  
    
    for i in range(1, len(lists)):
        formula_list.append(FormulaNode(signatures["Parallel"], [lists[i-1], lists[i]]))

def solveLines(boxes, graph_parse, delete_points, formula_list, log_message):
    points = get_all_instances(graph_parse, 'point')
    lines = get_all_instances(graph_parse, 'line')
    lists = []
    for box in boxes:
        mid = ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)
        choose, minlen = None, 999999
        for idx, pos in lines.items():
            if len(set(idx) & set(delete_points)) > 0: continue
            angle = calc_angle(pos[0], mid, pos[1])
            # The angle needs to approach pi (180).
            if angle >= math.pi - 0.2 and in_line(pos, mid):
                nowlen = dist(pos[0], mid) + dist(pos[1], mid)
                if nowlen < minlen:
                    minlen, choose = nowlen, idx
        if choose == None:
            log_message.append("Can not find the corresponding equal lines:" + str(box))
        else:
            for idx, pos in points.items():
                if not idx in choose and in_box(pos, box):
                    delete_points.append(idx)
            choose = [graph_parse.point_variables[x] for x in choose]
            assert len(choose) == 2
            lists.append(FormulaNode(signatures['LengthOf'], 
                                     [FormulaNode(signatures['Line'], choose)])) 
    for i in range(1, len(lists)):
        formula_list.append(FormulaNode(signatures["Equals"], [lists[i-1], lists[i]]))

def solveAngles(boxes, graph_parse, delete_points, formula_list, log_message):
    points = get_all_instances(graph_parse, 'point')
    angles = get_all_instances(graph_parse, 'angle')
    lists = []
    for box in boxes:
        mid = ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)
        choose, minlen = None, 999999
        for idx, pos in angles.items():
            if len(set(idx) & set(delete_points)) > 0: continue
            # The point [mid] must lie in the angle.
            #print (id, pos)
            #print (cross(pos[1], mid, pos[0]), cross(pos[1], mid, pos[2]))
            if cross(pos[1], mid, pos[0]) * cross(pos[1], mid, pos[2]) > 0: continue
            #print (in_line((pos[1], pos[0]), mid), in_line((pos[1], pos[2]), mid))
            if not in_line((pos[1], pos[0]), mid): continue
            if not in_line((pos[1], pos[2]), mid): continue
            nowlen= dist(pos[1], mid)
            if nowlen < minlen:
                minlen, choose = nowlen, idx
        if choose == None:
            log_message.append("Can not find the corresponding equal angles:" + str(box))
        else:
            for idx, pos in points.items():
                if not idx in choose and in_box(pos, box):
                    delete_points.append(idx)
            choose = [graph_parse.point_variables[x] for x in choose]
            assert len(choose) == 3
            lists.append(FormulaNode(signatures['MeasureOf'], 
                                     [FormulaNode(signatures['Angle'], choose)])) 
    for i in range(1, len(lists)):
        formula_list.append(FormulaNode(signatures["Equals"], [lists[i-1], lists[i]]))

def solveSigns(graph_parse, factor, sign_results, log_message):
    offset = graph_parse.image_segment_parse.diagram_image_segment.offset
    sign2box = {}
    for element in sign_results:
        label = element[4]
        if not label in sign2box:
            sign2box[label] = []
        element = (element[0] * factor[0] - offset.x, element[1] * factor[1] - offset.y,
                   element[2] * factor[0] - offset.x, element[3] * factor[1] - offset.y, element[4])
        sign2box[label].append(element)

    delete_points = []
    formula_list = []
    
    for key, value in sign2box.items():
        if key == "perpendicular":
            for element in value:
                solvePerpendicular(element, graph_parse, delete_points, formula_list, log_message)
    for key, value in sign2box.items():
        if key in ["parallel", "doubleparallel", "tripleparallel"]:
            solveParallels(value, graph_parse, delete_points, formula_list, log_message)
    for key, value in sign2box.items():
        if key in ["bar", "doublebar", "triplebar", "quadruplebar", "quadbar"]:
            solveLines(value, graph_parse, delete_points, formula_list, log_message)
    for key, value in sign2box.items():
        if key in ["angle", "doubleangle", "tripleangle", "quadrupleangle"]:
            solveAngles(value, graph_parse, delete_points, formula_list, log_message)
    return delete_points, formula_list