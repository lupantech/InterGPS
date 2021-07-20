import csv
import os
from geosolver.database.geoserver_interface import geoserver_interface

__author__ = 'minjoon'

def question_uploader_2(root_path, file_name="questions.csv"):
    """
    This is the uploader for the second data set collected by Isaac
    The root path contains "question.csv" file.
    headers are:
    image name, text, choice 1, choice 2, ... , choice 5, answer, ... , is multiple choice
    :param root_path:
    :return:
    """
    file_path = os.path.join(root_path, file_name)
    flag = False
    with open(file_path, 'rU') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', dialect=csv.excel_tab)
        reader.next()
        for row in reader:
            image_name = row[0]
            question_text = row[1]
            choices = row[2:7]
            answer = row[7]
            is_problematic = row[9] == '1'
            has_choices = row[10] == '1'
            has_answer = row[11] == '1'

            """
            if image_name == "0510.png":
                flag = True
            if not flag:
                continue
            """

            if is_problematic:
                continue

            if has_choices:
                answer = answer.split(" ")[1]
            else:
                choices = []

            image_path = os.path.join(root_path, image_name)
            geoserver_interface.upload_question(question_text, image_path, choices, answer)
            print(image_name)

if __name__ == "__main__":
    question_uploader_2("/Users/minjoon/Documents/data/geometry2/Questions")