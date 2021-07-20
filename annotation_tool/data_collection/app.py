# -*- coding: utf-8 -*-
import json
import base64

from flask import Flask, render_template, request, jsonify
from utilities import *

DATA_PATH  = "data_examples"


# Application entrance
app = Flask(__name__)

@app.route('/')
def index():
    name = listdir_(os.path.join(DATA_PATH))[-1] # num = 1
    return edit(name)

@app.route('/get_list/', methods=['GET'])
def get_list():
    dir = os.path.join(DATA_PATH)
    if os.path.exists(dir):
        return jsonify(listdir_(dir))
    else:
        return jsonify([])


# Read and display data
@app.route('/edit/<name>', methods=['GET'])
def edit(name):
    num = find_num(name, DATA_PATH)    # data number: 10

    names = listdir_(os.path.join(DATA_PATH))
    sorted_names = sorted(names)
    previous_name = sorted_names[max(0, sorted_names.index(name)-1)]
    print("\ncurrent name: ", name)
    print("previous name: ", previous_name)

    if num != -1:
        dir = os.path.join(DATA_PATH, name)
        print(dir)
        with open(os.path.join(dir, 'img_problem.png'), 'rb') as f1, \
             open(os.path.join(dir, 'img_diagram_point.png'), 'rb') as f2, \
             open(os.path.join(dir, 'data.json'), 'r') as json_file, \
             open(os.path.join(dir, 'logic_form.json')) as logic_file:

            head = "data:image/png;base64,"
            f1_b64 = str(base64.b64encode(f1.read()))[2:-1]  # remove b'' decorator
            f2_b64 = str(base64.b64encode(f2.read()))[2:-1]

            data = json.load(json_file)
            logic_form = json.load(logic_file)
            data["img1"] = head + f1_b64
            data["img2"] = head + f2_b64

            # load previous logic forms
            pre_dir = os.path.join(DATA_PATH, previous_name)
            with open(os.path.join(pre_dir, 'logic_form.json')) as logic_file2:
                previous_logic_form = json.load(logic_file2)

            return render_template('edit.html',
                                annot_num = num, # 1-750
                                name = name,     # problem id: [0, 3001]
                                data = data,     # text, images
                                logic_forms = logic_form, # logic forms
                                previous_logic_forms = previous_logic_form,  # previous logic forms
                                names = names)

    return "Annotation not found, could be deleted" # Failure


## Extract and save edited data
@app.route('/edit/<name>', methods=['POST'])
def edit_submit(name):
    if find_num(name, DATA_PATH) == -1:
        return 404
    else:
        print('POST')
        data = dict(request.form) # from form.html

        problem_text = data["problem_text"]
        answer = data["answer"]
        comment = data["comment"]
        pid = name  # problem id
        text_logic_form = data["text_logic_form"]
        dissolved_text_logic_form = data["dissolved_text_logic_form"]
        diagram_logic_form = data["diagram_logic_form"]
        line_instances = data["line_instances"]
        circle_instances = data["circle_instances"]
        point_positions = data["point_positions"]
        next_name = data["next_name"]
 
        choices = []
        for i in range(4):
            choice_value = data["choices"+str(i+1)]
            if choice_value != '':
                choices.append(choice_value)
        
        problem_type_graph = []
        for i in range(9):
            type_name = "graph_type"+str(i+1)
            if type_name in data:
                problem_type_graph.append(data[type_name])

        problem_type_goal = []
        for i in range(5):
            type_name = "goal_type"+str(i+1)
            if type_name in data:
                problem_type_goal.append(data[type_name])

        # check and make the output directory
        output_path = "{}/{}/".format(DATA_PATH, pid) # data_examples/11

        text_logic_form = text_logic_form.split("\r\n")
        dissolved_text_logic_form = dissolved_text_logic_form.split("\r\n")
        diagram_logic_form = diagram_logic_form.split("\r\n")
        line_instances = line_instances.split("\r\n")
        circle_instances = circle_instances.split("\r\n")
        point_positions = point_positions.split("\r\n") # ['A: 1, 2', 'B: 2, 3']
        new_point_positions = {}
        print (point_positions)
        for element in point_positions:
            print (element)
            data1 = element.split(": ")
            data2 = data1[1].split(', ')
            new_point_positions[data1[0]] = [float(data2[0]), float(data2[1])]

        # save data to json file
        json_path = output_path + 'data.json'
        with open(json_path) as f:
            raw_data = json.load(f)

        # raw_data["problem_text"] = problem_text  # save to "problem_text"
        raw_data["annotat_text"] = problem_text  # problem text with latex expressions
        raw_data["choices"] = choices
        raw_data["answer"] = answer[0]
        raw_data["problem_type_graph"] = problem_type_graph
        raw_data["problem_type_goal"] = problem_type_goal
        raw_data["comment"] =  comment

        print (raw_data["answer"])
        with open(json_path, 'w') as f:
            json.dump(raw_data, f, indent = 2, separators=(',', ': '))

        # save logic forms to json file
        logic_forms = {
            "text_logic_form": text_logic_form,
            "dissolved_text_logic_form": dissolved_text_logic_form,
            "diagram_logic_form": diagram_logic_form,
            "line_instances": line_instances,
            "point_positions": new_point_positions,
            "circle_instances": circle_instances
        }
        json_path = output_path + 'logic_form.json'
        with open(json_path, 'w') as f:
            json.dump(logic_forms, f, indent = 2, separators=(',', ': '))

        # next data
        if next_name:
            return edit(next_name)
        else:
            return edit(name)

    return 404


@app.route('/redirect', methods=['GET'])
def redirect_message():
    msg = request.args.get('message')
    url = request.args.get('url')
    return render_template('success.html', message=msg, url=url)


if __name__ == '__main__':
    # app.run()
    app.run(host='localhost', port=5000, debug=True)

