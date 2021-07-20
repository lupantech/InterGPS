import os
import json
import time
import random
import warnings
import argparse

from numpy.random import seed
from extended_definition import ExtendedDefinition
from logic_parser import LogicParser
from logic_solver import LogicSolver
from func_timeout import func_timeout, FunctionTimedOut
from tqdm import tqdm
from multiprocess import Pool

warnings.filterwarnings('ignore')

seed(0)
random.seed(0)


def getParameters():
    parser = argparse.ArgumentParser(description="Welcome to use GeoSolver!")

    # experiment label and strategy
    parser.add_argument("--label", type=str, required=True, help="the label of current experiment")
    parser.add_argument("--strategy", type=str, choices = ['random', 'low-first', 'predict', 'final'],
                        help="different search strategies")

    # input data
    parser.add_argument("--data_path", type=str, default="../data/geometry3k", help="the path of geometry3k")
    parser.add_argument("--text_logic_form_path", type=str, help="the path of text logic forms")
    parser.add_argument("--diagram_logic_form_path", type=str, help="the path of diagram logic forms")

    # important parameters for the symbolic solver
    parser.add_argument("--use_annotated", action="store_true", help="use annotated data instead of generated data")
    parser.add_argument("--predict_path", type=str, help="the predict sequence for the solver")
    parser.add_argument("--start_index", type=int, default=2401, help="the start point of testing data")
    parser.add_argument("--end_index", type=int, default=3001, help="the end point of testing data")
    parser.add_argument("--time_limit", type=int, default=150, help="the seconds of time limit")
    parser.add_argument("--num_threads", type=int, default=20, help="the number of running threads, recommendation: # of CPU threads")

    args = parser.parse_args()

    # theorem sequences
    if args.predict_path is None:
        if args.strategy == "final":
            args.predict_path = "../theorem_predict/results/test/pred_seq_result_bart_epoch19_seq5.json"
        elif args.strategy == "random":
            args.predict_path = "../theorem_predict/results/test/pred_seqs_test_l100_random.json"
        elif args.strategy == "predict":
            args.predict_path = "../theorem_predict/results/test/pred_seq_result_bart_epoch19_seq5_add_random.json"

    # text logic forms
    if args.text_logic_form_path is None:
        if args.use_annotated:
            args.text_logic_form_path = "../data/geometry3k/logic_forms/text_logic_forms_annot_dissolved.json"
        else:
            args.text_logic_form_path = "../text_parser/text_logic_forms_pred.json"

    # diagram logic forms
    if args.diagram_logic_form_path is None:
        if args.use_annotated:
            args.diagram_logic_form_path = "../data/geometry3k/logic_forms/diagram_logic_forms_annot.json"
        else:
            args.diagram_logic_form_path = "../diagram_parser/diagram_logic_forms_pred.json"

    args.low_first = args.strategy in ["low-first", "final"] # apply the low-first search strategy
    args.step_limit = 100 # the maximum search steps
    args.debug_mode = False # debug mode
    args.enable_round = False
    args.enable_predict = True

    return args


def solve_one_problem(args, text_parser, diagram_parser, order_lst):

    ## Set up the logic parser
    parser = LogicParser(ExtendedDefinition(debug=args.debug_mode))

    if diagram_parser is not None:
        # Define diagram primitive elements
        parser.logic.point_positions = diagram_parser['point_positions']

        isLetter = lambda ch: ch.upper() and len(ch) == 1
        parser.logic.define_point([_ for _ in parser.logic.point_positions if isLetter(_)])
        if args.debug_mode:
            print(parser.logic.point_positions)

        lines = diagram_parser['line_instances']  # ['AB', 'AC', 'AD', 'BC', 'BD', 'CD']
        for line in lines:
            line = line.strip()
            if len(line) == 2 and isLetter(line[0]) and isLetter(line[1]):
                parser.logic.define_line(line[0], line[1])

        circles = diagram_parser['circle_instances']  # ['O']
        for point in circles:
            parser.logic.define_circle(point)

        # Parse diagram logic forms
        logic_forms = diagram_parser['diagram_logic_forms']
        logic_forms = sorted(logic_forms, key=lambda x: x.find("Perpendicular") != -1)  # put 'Perpendicular' to the end

        for logic_form in logic_forms:
            if logic_form.strip() != "":
                if args.debug_mode:
                    print("The diagram logic form is", logic_form)
                try:
                    parse_tree = parser.parse(logic_form) # ['Equals', ['LengthOf', ['Line', 'A', 'C']], '10']
                    parser.dfsParseTree(parse_tree)
                except Exception as e:
                    if args.debug_mode:
                        print("\033[0;0;41mError:\033[0m", repr(e))

    ## Parse text logic forms
    target = None
    text_logic_forms = text_parser["text_logic_forms"]
    for text in text_logic_forms:
        if args.debug_mode:
            print("The text logic form is", text)
        if text.find('Find') != -1:
            target = parser.findTarget(parser.parse(text)) # ['Value', 'A', 'C']
        else:
            res = parser.parse(text)
            parser.dfsParseTree(res)

    if args.debug_mode:
        print("The predicting sequence is", order_lst)

    ## Set up, initialize and run the logic solver
    solver = LogicSolver(parser.logic)
    solver.initSearch()
    answer, steps, step_lst = solver.Search(target=target,
                                            order_list=order_lst,
                                            round_or_step=args.enable_round,
                                            upper_bound=args.round_limit if args.enable_round else args.step_limit,
                                            enable_low_first=args.low_first)

    return target, answer, steps, step_lst


def multithread_solve(parameters):

    index, args, text_logic_form, diagram_logic_form, order_lst = parameters
    target, answer, steps, step_lst = None, None, 0, []

    # solve the #index problem
    solve_problem_start = time.time()
    if args.debug_mode:
        target, answer, steps, step_lst = solve_one_problem(args, text_logic_form, diagram_logic_form, order_lst)
    else:
        try:
            target, answer, steps, step_lst = func_timeout(args.time_limit, solve_one_problem,
                                                           kwargs=dict(args=args,
                                                                 text_parser=text_logic_form,
                                                                 diagram_parser=diagram_logic_form,
                                                                 order_lst=order_lst))
        except FunctionTimedOut:
            pass
        except Exception as e:
            if args.debug_mode:
                print("\033[0;0;41mError:\033[0m", repr(e))
    time_interval = time.time() - solve_problem_start

    # solved result
    answer = float(answer) if answer is not None else answer
    entry = {'pid': index, 'target': target, 'guess': answer, 'correctness': 'no',
             'steps': steps, 'step_lst': step_lst, 'time': round(time_interval, 2)}

    # ground truth
    data_json = json.load(open(os.path.join(args.data_path, 'test', str(index), "data.json")))
    value_list = data_json['precise_value']  # [5.0, 12.0, 13.0, 26.0]
    gt_id = ord(data_json['answer']) - 65  # 0

    # validate the predicted answer
    if answer is not None:
        # all choice candidates are valid, and the answer is the closest one to ground truth among choice candidates
        try:
            if all([x is not None for x in value_list]) and \
                    abs(value_list[gt_id] - answer) == min([abs(x - answer) for x in value_list]):
                entry['correctness'] = 'yes'
        except Exception as e:
            if args.debug_mode:
                print("\035[0;0;41mError:\0353[0m", repr(e), value_list, gt_id, answer)
        if entry['correctness'] == 'yes':
            if args.debug_mode:
                print("\033[0;0;42mCorrect_answer:\033[0m ", end="")  # green
        else:
            if args.debug_mode:
                print("\033[0;0;43mWrong_answer:\033[0m ", end="")  # yellow

    if args.debug_mode:
        print(entry)
    return entry


if __name__ == '__main__':

    args = getParameters()

    ## Load files
    text_logic_table = json.load(open(args.text_logic_form_path, "r"))

    diagram_logic_table = None
    if args.diagram_logic_form_path is not None:
        diagram_logic_table = json.load(open(args.diagram_logic_form_path, "r"))

    predict_table = None
    if args.predict_path is not None:
        predict_table = json.load(open(args.predict_path, "r"))

    lst = list(range(args.start_index, args.end_index + 1)) # range(2401, 3002)

    ## Read logic forms and predicated theorem orders
    para_lst = []
    for index in lst:
        str_index = str(index)
        text_logic_form, diagram_logic_form, order_lst = None, None, None

        if text_logic_table is not None:
            text_logic_form = text_logic_table.get(str_index)

        if diagram_logic_table is not None:
            diagram_logic_form = diagram_logic_table.get(str_index)

        if args.enable_predict and predict_table is not None:
            if str_index in predict_table:
                order_lst = predict_table[str_index]['seq']
                if isinstance(order_lst[0], list):
                    order_lst = order_lst[0]

        para_lst.append((index, args, text_logic_form, diagram_logic_form, order_lst))

    ## Run the solver and save results
    if args.debug_mode:
        for paras in para_lst:
            multithread_solve(paras)
    else:
        solve_all_problems_start = time.time()

        argsDict = args.__dict__
        for arg in argsDict.keys():
            print("%24s = %s" % (arg, argsDict[arg]))

        # run the solver with multiple threads
        solve_list = []
        with tqdm(total=len(para_lst), ncols=80) as t:
            with Pool(args.num_threads) as p:
                for answer in p.imap_unordered(multithread_solve, para_lst):
                    solve_list.append(answer)
                    t.update()

        solve_list = sorted(solve_list, key=lambda x: int(x['pid']))
        solve_all_problems_end = time.time()

        # print and save solving process
        date = time.strftime("_%Y-%m-%d_%H_%M_%Z", time.localtime())
        label = str(int(time.time())) + "-" + args.label
        log_file = open("logs/log-{}.log".format(label), "w")

        for arg in argsDict.keys():
            print("%24s = %s" % (arg, argsDict[arg]), file=log_file)

        print(file=log_file)
        for data in solve_list:
            print(data, file=log_file)
        print(file=log_file)

        # analyze solved problems
        print("\nFinished, calculating solved problems...")

        solved_list = [x['pid'] for x in solve_list if x['guess'] is not None]
        solved_correct_list = [x['pid'] for x in solve_list if x['correctness'] == 'yes']
        solved_wrong_list = [num for num in solved_list if num not in solved_correct_list]
        unsolved_list = [num for num in lst if num not in solved_list]

        num_solved = len(solved_list)
        num_solved_correct = len(solved_correct_list)
        num_solved_wrong = len(solved_wrong_list)
        num_guessed_correct = num_solved_correct + (len(lst) - num_solved) * 0.25

        avg_solve_step = sum([x['steps'] for x in solve_list]) / max(num_solved, 1)
        avg_solved_step = sum([x['steps'] for x in solve_list if x['guess'] is not None]) / max(num_solved, 1)
        avg_solve_time = sum([x['time'] for x in solve_list]) / max(num_solved, 1)
        avg_solved_time = sum([x['time'] for x in solve_list if x['guess'] is not None]) / max(num_solved, 1)
        real_time = round(solve_all_problems_end - solve_all_problems_start)

        # print results
        print("Solved list: ", solved_list, file=log_file)
        print("Solved and correct list: ", solved_correct_list, file=log_file)
        print("Solved but wrong list: ", solved_wrong_list, file=log_file)
        print("Unsolved list: ", unsolved_list, file=log_file)
        print(file=log_file)

        for item in ["num_solved", "num_solved_correct", "num_solved_wrong", "num_guessed_correct"]:
            print("{}: {} ({:.2f}%)".format(item, eval(item), eval(item) / len(lst) * 100), file=log_file)
            print("{}: {} ({:.2f}%)".format(item, eval(item), eval(item) / len(lst) * 100))
        print(file=log_file)

        print("Average steps for all problems: {:.2f}".format(avg_solve_step), file=log_file)
        print("Average steps for solved problems: {:.2f}".format(avg_solved_step), file=log_file)
        print("Average steps for solved problems: {:.2f}".format(avg_solved_step))
        print("Average time for all problems: {:.2f} seconds".format(avg_solve_time), file=log_file)
        print("Average time for solved problems: {:.2f} seconds".format(avg_solved_time), file=log_file)
        print("Real total time: {} seconds".format(real_time), file=log_file)
        print("Done.")

        # save results
        results = {}

        for res in solve_list:
            res['target'] = str(res['target']) # fix TypeError (Object of type 'ParseResults' is not JSON serializable)

        results['result'] = solve_list # result entries

        results['test_list'] = lst # test problem ids: [2401, 2402, ..., 3001]
        results['solved_list'] = solved_list
        results['solved_correct_list'] = solved_correct_list
        results['solved_wrong_list'] = solved_wrong_list
        results['unsolved_list'] = unsolved_list

        results['avg_solve_time'] = avg_solve_time
        results['avg_solved_time'] = avg_solved_time
        results['avg_solve_step'] = avg_solve_step
        results['avg_solved_step'] = avg_solved_step
        results['real_time'] = real_time

        results['problem_data_version'] = str(args.data_path)
        results['text_logic_version'] = str(args.text_logic_form_path)
        results['diagram_logic_version'] = str(args.diagram_logic_form_path)

        print("Saving logging file to:", "logs/log-{}.log".format(label))
        print("Saving result file to:", "pred_results/logic_{}.json".format(label))
        with open("pred_results/logic_{}.json".format(label), 'w') as f:
            json.dump(results, f, indent=2, separators=(',', ': '))

