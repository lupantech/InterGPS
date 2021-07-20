import time
import os
import json
import sys
import argparse

sys.path.append("vanilla_symbolic_solver")
from run_solver import LogicSolver
from extended_definition import ExtendedDefinition
from logic_parser import LogicParser
from multiprocessing import Pool
from func_timeout import func_timeout, FunctionTimedOut

import random
random.seed(0)


def isLetter(ch):
    return ch.upper() and len(ch) == 1


def solve_with_text_and_diagram(diagram_parser, text_parser, order_lst, debug=False):
    ## Set up the logic parser
    parser = LogicParser(ExtendedDefinition(debug=debug))

    ## Define diagram primitive elements
    parser.logic.point_positions = diagram_parser['point_positions']
    parser.logic.define_point([p for p in parser.logic.point_positions if isLetter(p)])
    if parser.logic.debug:
        print(parser.logic.point_positions)

    lines = diagram_parser['line_instances']  # ['AB', 'AC', 'AD', 'BC', 'BD', 'CD']
    for line in lines:
        line = line.strip()
        if len(line) == 2 and isLetter(line[0]) and isLetter(line[1]):
            parser.logic.define_line(line[0], line[1])

    circles = diagram_parser['circle_instances']  # ['O']
    for point in circles:
        parser.logic.define_circle(point)

    ## Parse diagram logic forms
    logic_forms = diagram_parser['diagram_logic_forms']
    logic_forms = sorted(logic_forms, key=lambda x: x.find("Perpendicular") != -1)  # put 'Perpendicular' to the end

    for logic_form in logic_forms:
        if logic_form.strip() != "":
            if parser.logic.debug:
                print("The diagram logic form is", logic_form)
            try:
                res = parser.parse(logic_form) # e.g., ['Equals', ['LengthOf', ['Line', 'A', 'C']], '10']
                parser.dfsParseTree(res)
            except Exception as e:
                # print("\033[0;0;41mError:\033[0m", repr(e))
                pass

    ## Parse text logic forms
    target = None
    text_logic_forms = text_parser["text_logic_forms"]
    for text in text_logic_forms:
        if parser.logic.debug:
            print("The text logic form is", text)
        if text.find('Find') != -1:
            target = parser.findTarget(parser.parse(text))  # ['Value', 'A', 'C']
        else:
            res = parser.parse(text)
            parser.dfsParseTree(res)

    ## Set up, initialize and apply the logic solver
    solver = LogicSolver(parser.logic)
    solver.initSearch()
    answer, steps, step_lst = solver.Search(target, order_lst)  # 60.0 / None

    return target, answer, steps, step_lst


def solve(index_start, debug=False):

    # data splits
    if index_start in range(2101):
        split = 'train'
    elif index_start in range(2101, 2401):
        split = 'val'
    else:
        split = 'test'

    id = str(index_start)
    target, answer, steps, step_lst = None, None, 0, []
    clock_start = time.time()

    ## Search for target and answer
    if use_predict_order:
        order_lst = pred_seq_table[id]['seqs'][try_id]
        # print(order_lst)
    else:
        order_lst = None

    try:
        target, answer, steps, step_lst = func_timeout(150, solve_with_text_and_diagram,
                                                 kwargs=dict(diagram_parser=diagram_logic_table[id],
                                                             text_parser=text_logic_table[id],
                                                             order_lst=order_lst))
    except FunctionTimedOut:
        pass
    except Exception as e:
        # print("\033[0;0;41mError:\033[0m", repr(e))
        pass

    time_interval = time.time() - clock_start
    try:
        answer = float(answer) if answer is not None else answer
    except Exception as e:
        pass
    entry = {'num': id, 'target': target, 'guess': answer, 'correctness': 'no',
             'steps': steps, 'step_lst': step_lst, 'time': round(time_interval, 2)}

    ## Validate the predicted answer
    if answer is not None:
        ANSWER_INPUT_PATH = os.path.join(DATA_INPUT_PATH, split, id, "data.json")
        with open(ANSWER_INPUT_PATH, "r") as f:
            data = json.load(f)
        value_list = data['precise_value']  # ! e.g., [5.0, 12.0, 13.0, 26.0]
        gt_id = ord(data['answer']) - 65  # e.g., 0

        # all choice candidates are valid, and the answer is the closest one to ground truth among choice candidates
        try:
            if all([x is not None for x in value_list]) and \
                    abs(value_list[gt_id] - answer) == min([abs(x - answer) for x in value_list]):
                entry['correctness'] = 'yes'
        except Exception as e:
            # print("\035[0;0;41mError:\0353[0m", repr(e), value_list, gt_id, answer)
            pass

        if entry['correctness'] == 'yes':
            print("\033[0;0;42mCorrect_answer:\033[0m ", end="")  # green
        # else:
        #     print("\033[0;0;43mWrong_answer:\033[0m ", end="")  # yellow

    if entry['correctness'] == 'yes':
        print(entry)

    return entry



def one_try(try_id):
    try:

        print("\nTry:", try_id)
        print("\nTry:", try_id, file=log_file)

        clock_start = time.time()
        with Pool(cpu_cores) as p:
            solve_list = p.map(solve, lst)  # multiple processing pools for 'solve' over 'lst'
        for data in solve_list:
            if data['correctness'] == 'yes':
                print(data, file=log_file)
        clock_end = time.time()

        ## Analyze solved problems
        print("\nFinished, calculating solved problems...")

        solved_list = [x['num'] for x in solve_list if x['guess'] is not None]
        solved_correct_list = [x['num'] for x in solve_list if x['correctness'] == 'yes']
        solved_wrong_list = [num for num in solved_list if num not in solved_correct_list]
        unsolved_list = [str(num) for num in lst if str(num) not in solved_list]

        assert len(solved_list) == len(solved_correct_list) + len(solved_wrong_list)
        assert len(lst) == len(solved_list) + len(unsolved_list)

        num_solved = len(solved_list)
        num_solved_correct = len(solved_correct_list)
        num_solved_wrong = len(solved_wrong_list)

        avg_step = sum([x['steps'] for x in solve_list]) / len(solved_list)
        total_time = int(sum([x['time'] for x in solve_list]))
        real_time = int(clock_end - clock_start)

        print("\nSolved list: ", solved_list, file=log_file)
        print("Solved and correct wrong list: ", solved_correct_list, file=log_file)
        print("Solved but wrong list: ", solved_wrong_list, file=log_file)
        print("Unsolved list: ", unsolved_list, file=log_file)

        print("\nThe number of problems solved: {} ({:.2f}%)".format(num_solved, num_solved / len(lst) * 100),
              file=log_file)
        print("The number of problems correctly solved: {} ({:.2f}%)".format(num_solved_correct,
                                                                             num_solved_correct / len(lst) * 100),
              file=log_file)
        print("The number of problems wrongly solved: {} ({:.2f}%)".format(num_solved_wrong,
                                                                           num_solved_wrong / len(lst) * 100),
              file=log_file)

        print("\nAverage steps: {:.2f}".format(avg_step), file=log_file)
        print("Total time: {} seconds".format(total_time), file=log_file)
        print("Real total time: {} seconds".format(real_time), file=log_file)

        ## Generate results
        results = {}
        for res in solve_list:
            if res['correctness'] == 'yes':
                pid = res['num']
                results[pid] = {'seq':res['step_lst'], 'status':'correct', 'time':res['time']}
        #print(results)

        # Save result.json file
        JSON_FILE = OUTPUT_PATH + "/pred_seqs_correct_try{}.json".format(try_id)
        with open(JSON_FILE, 'w') as f:
            json.dump(results, f, indent=2, separators=(',', ': '))
        print("Done.")

        return try_id

    except:
        return -1


if __name__ == '__main__':

    DATA_INPUT_PATH = '../../data/geometry3k'
    DIAGRAM_INPUT_PATH = '../../data/geometry3k/logic_forms/diagram_logic_forms_annot.json'
    TEXT_INPUT_PATH = '../../data/geometry3k/logic_forms/text_logic_forms_annot_dissolved.json'
    PREDICT_STEP_PATH = '../results/train/pred_seqs_train_l30_n100_template.json'

    OUTPUT_PATH = '../results/train/splits'
    LOG_PATH = '../results/train/logs'

    os.makedirs(OUTPUT_PATH, exist_ok=True)
    os.makedirs(LOG_PATH, exist_ok=True)

    use_predict_order = True

    parser = argparse.ArgumentParser()
    parser.add_argument('--try_num', type=int, default=100,
                        help='number of tries, larger tries are better but cost more time')
    parser.add_argument('--cpu_cores', type=int, default=10,
                        help='number of cpu cores, used for multi-core accelerating')

    args = parser.parse_args()

    try_num = args.try_num
    cpu_cores = args.cpu_cores

    with open(DIAGRAM_INPUT_PATH, "r") as f1:
        diagram_logic_table = json.load(f1)
    with open(TEXT_INPUT_PATH, "r") as f2:
        text_logic_table = json.load(f2)

    if use_predict_order:
        with open(PREDICT_STEP_PATH, "r") as f:
            pred_seq_table = json.load(f)

    date = time.strftime("_%Y-%m-%d_%H_%M_%Z", time.localtime())
    label = str(int(time.time())) #+ date
    LOG_FILE = "{}/log-{}.log".format(LOG_PATH, label)
    log_file = open(LOG_FILE, "w")

    print(label + '\n', file=log_file)
    print("problem data version: ", DATA_INPUT_PATH, file=log_file)
    print("text logic form version: ", TEXT_INPUT_PATH, file=log_file)
    print("diagram logic form version: ", DIAGRAM_INPUT_PATH, file=log_file)
    if use_predict_order: print("use predict order.", PREDICT_STEP_PATH, '\n', file=log_file)

    ## To solve problem
    lst = list(range(2401))  # train + val list: [0,2400]

    success_ids = []
    for try_id in range(try_num):
        status = one_try(try_id) # go over all 2401 problems once
        success_ids.append(status)

    ## Check and rerun failed cases
    failure = [id for id in range(try_num) if id not in success_ids]
    if len(failure) > 0:
        for try_id in failure:
            success = one_try(try_id)  # go over all 2401 problems once

