import json
import math
import random
import os
import argparse


def quad_alias(diagram_type, QuadAlias):
    alias_diagram_type = []
    for diagram in diagram_type:
        if diagram in QuadAlias:
            diagram = QuadAlias[diagram]
        alias_diagram_type.append(diagram)
    return(alias_diagram_type)


def correct_goal_type(goal_type):
    if "Other" in goal_type and len(goal_type) > 1:
        goal_type.remove("Other")
    return goal_type


def build_dict(data_path):

    file_list = os.listdir(data_path)
    if ".DS_Store" in file_list:
        file_list.remove('.DS_Store')

    IdToGoalType = {}
    IdToDiagramType = {}
    GoalTypeToId = {}
    DiagramTypeToId = {}

    QuadAlias = {}
    Quads = ["Rectangle", "Rhombus", "Parallelogram", "Trapezoid", "Square"]
    for quad in Quads:
        QuadAlias[quad] = "Quad"

    for idx, data_id in enumerate(file_list):
        with open(os.path.join(data_path, data_id, "data.json"), 'r') as f:
            data = json.load(f)

        if data["data_type"] == "test":
            pid = data["id"]

            # IdToGoalType, GoalTypeToId
            goal_type = data["problem_type_goal"]
            goal_type = correct_goal_type(goal_type)

            IdToGoalType[pid] = goal_type
            for goal in goal_type:
                if goal in GoalTypeToId:
                    GoalTypeToId[goal].append(pid)
                else:
                    GoalTypeToId[goal] = [pid]

            # IdToDiagramType, DiagramTypeToId
            diagram_type = data["problem_type_graph"]
            diagram_type = quad_alias(diagram_type, QuadAlias)

            IdToDiagramType[pid] = diagram_type

            for diagram in diagram_type:
                if diagram in DiagramTypeToId:
                    DiagramTypeToId[diagram].append(pid)
                else:
                    DiagramTypeToId[diagram] = [pid]

    assert len(IdToGoalType) == 601
    assert len(IdToDiagramType) == 601

    return IdToGoalType, IdToDiagramType, GoalTypeToId, DiagramTypeToId


def print_type_acc(Result_Acc):
    Acc_GoalTypeToId = {}
    Acc_DiagramTypeToId = {}

    for pid in Result_Acc:
        # goal type acc 
        goal_type = IdToGoalType[pid]
        goal_type = correct_goal_type(goal_type)
        for goal in goal_type:
            if goal in Acc_GoalTypeToId:
                Acc_GoalTypeToId[goal].append(pid)
            else:
                Acc_GoalTypeToId[goal] = [pid]            

        # diagram type acc 
        diagram_type = IdToDiagramType[pid]
        for diagram in diagram_type:
            if diagram in Acc_DiagramTypeToId:
                Acc_DiagramTypeToId[diagram].append(pid)
            else:
                Acc_DiagramTypeToId[diagram] = [pid]

    Angle  = 100*len(Acc_GoalTypeToId["Angle"])/len(GoalTypeToId["Angle"])
    Length = 100*len(Acc_GoalTypeToId["Length"])/len(GoalTypeToId["Length"])
    Area   = 100*len(Acc_GoalTypeToId["Area"])/len(GoalTypeToId["Area"])
    Ratio  = 100*len(Acc_GoalTypeToId["Ratio"])/len(GoalTypeToId["Ratio"])
    
    Line  = 100*len(Acc_DiagramTypeToId["Line"])/len(DiagramTypeToId["Line"])
    Triangle  = 100*len(Acc_DiagramTypeToId["Triangle"])/len(DiagramTypeToId["Triangle"])
    Quad  = 100*len(Acc_DiagramTypeToId["Quad"])/len(DiagramTypeToId["Quad"])
    Circle  = 100*len(Acc_DiagramTypeToId["Circle"])/len(DiagramTypeToId["Circle"])
    Other  = 100*len(Acc_DiagramTypeToId["Other"])/len(DiagramTypeToId["Other"])

    # latex type
    print("[Sub Acc]: &{:.3} &{:.3} &{:.3} &{:.3} &{:.3} &{:.3} &{:.3} &{:.3} &{:.3} \\\\".format(
                      Angle, Length, Area, Ratio, Line, Triangle, Quad, Circle, Other))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Accuracies for different problem types.')
    parser.add_argument('--result_file', type=str, help='Path to the result file')
    args = parser.parse_args()

    DATA_PATH = '../data/geometry3k/test'

    IdToGoalType, IdToDiagramType, GoalTypeToId, DiagramTypeToId = build_dict(DATA_PATH)

    # read the result json file
    result_data = json.load(open(args.result_file))
    TestId = result_data['test_list']
    assert len(TestId) == 601

    # compute acc
    solved_correct_list = result_data['solved_correct_list']
    unsolved_list = result_data['unsolved_list']
    guess_correct_list = random.sample(unsolved_list, math.ceil(len(unsolved_list) / 4))

    Acc = solved_correct_list + guess_correct_list
    Acc = [int(id) for id in Acc]
    correct = len(Acc)

    print("[File]:\t  ", args.result_file)
    print("[Acc]:\t   {}/{} = {:.2%}".format(correct, 601, correct / 601))
    print_type_acc(Acc)

