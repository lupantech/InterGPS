import json
import shutil
import sys
import os
from geosolver import geoserver_interface
from geosolver.database.utils import zip_diagrams
from geosolver.utils.prep import get_number_string

__author__ = 'minjoon'

def test_geoserver_interface():
    data = geoserver_interface.download_questions(["annotated"])
    ann = geoserver_interface.download_semantics()
    print(ann)
    print(data)


def test_zip_diagrams():
    questions = geoserver_interface.download_questions(['development'])
    zip_diagrams(questions, '/Users/minjoon/Desktop/development.zip')


def save_questions(query):
    questions = geoserver_interface.download_questions(query)
    base_path = os.path.join("../../temp/data/", query)
    if not os.path.exists(base_path):
        os.mkdir(base_path)
    for index, (key, question) in enumerate(questions.iteritems()):
        print key
        folder_name = get_number_string(index, 3)
        json_path = os.path.join(base_path, folder_name + ".json")
        diagram_path = os.path.join(base_path, folder_name + ".png")
        d = {}
        d['key'] = question.key
        d['text'] = question.text
        d['choices'] = question.choices
        d['answer'] = str(int(question.answer))
        json.dump(d, open(json_path, 'wb'))
        shutil.copyfile(question.diagram_path, diagram_path)




if __name__ == "__main__":
    # test_geoserver_interface()
    # test_zip_diagrams()
    save_questions('aaai')
    save_questions('practice')
    save_questions('official')