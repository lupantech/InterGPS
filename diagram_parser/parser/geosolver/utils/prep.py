"""
Preprocessing utils to obtain appropriate format for question text and diagram.
"""
import os
import tempfile
import re

import cv2
import networkx as nx
from PIL import Image
import requests
from geosolver import settings

__author__ = 'minjoon'


def save_graph_image(graph, path):
    pydot_graph = nx.to_pydot(graph)
    pydot_graph.write_png(path)


def get_graph_image(graph):
    """
    Returns an image of graph.
    Currently not optimized, as it saves to a parse_match_from_known_labels directory then loads it again.
    If direct conversion to image is found for pydot_graph, please implement it instead.

    :param nx.Graph graph:
    :return np.ndarray:
    """
    _, path = tempfile.mkstemp()
    save_graph_image(graph, path)
    image = cv2.imread(path)
    return image


def display_graph(graph, method='image', title="", block=True):
    """
    Display the graph on the screen.
    Method can be 'image' or 'pyplot'.
    'image' method uses cv2 to display the image file.
    'pyplot' method uses matplotlib to draw the graph on pyplot (not implemented yet).

    :param graph:
    :param method:
    :return:
    """
    if method == 'image':
        image = get_graph_image(graph)
        cv2.imshow(title, image)
        if block:
            block_display()


def display_graphs(graphs, method='image', block=True):
    for graph in graphs:
        display_graph(graph, method=method, block=False)
    if block:
        block_display()


def block_display():
    cv2.waitKey()
    cv2.destroyAllWindows()


def open_image(filepath, grayscale=True):
    basepath, ext = os.path.splitext(filepath)
    if ext != ".png":
        newpath = basepath + ".png"
        fp = Image.open(filepath)
        fp.save(newpath)
        filepath = newpath
    if grayscale:
        image = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
    else:
        image = cv2.imread(filepath, cv2.IMREAD_COLOR)
    return image

def open_image_from_file(file, grayscale=True):
    fp = Image.open(file)
    _, path = tempfile.mkstemp(suffix=".png")
    fp.save(path)
    if grayscale:
        image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    else:
        image = cv2.imread(path, cv2.IMREAD_COLOR)
    return image


def save_image(image, ext=".png"):
    fp, filepath = tempfile.mkstemp(suffix=ext)
    cv2.imwrite(filepath, image)
    return fp, filepath


def display_image(image, title="", block=True):
    cv2.imshow(title, image)
    if block:
        block_display()


def get_number_string(n, w):
    """

    :param int n: number to be formatted
    :param int w: width of the number (w of 0004 is 4)
    :return str:
    """
    return ("{0:0%d}" % w).format(n)

def index_by_list(data, indices):
    out = data
    for index in indices:
        out = out[index]
    return out

def stanford_tokenizer(paragraph, server_url=None):
    if server_url is None:
        server_url = settings.STANFORD_TOKENIZER_URL
    print (paragraph)
    params = {"paragraph": paragraph}
    r = requests.get(server_url, params=params)
    print(r.url)
    data = r.json()
    return {sentence_idx: {idx: str(word) for idx, word in enumerate(sentence)}
            for sentence_idx, sentence in enumerate(data)}


def paragraph_to_sentences(paragraph):
    sentence_list = re.split('(?<=[.!?;]) +', paragraph)
    return dict(enumerate(sentence_list))


def sentence_to_words_statements_values(sentence):
    raw_words = re.split(r'(\\[a-zA-Z]+| |, |[.!?;]$|[()\+\-\*/^=><\{}|:])', sentence)
    raw_words = [word for word in raw_words if len(word.rstrip()) > 0]
    flags = [0]*len(raw_words)
    for idx in range(len(flags)):
        word = raw_words[idx]
        if word in "{":
            flags[idx] = 1
            if idx < len(raw_words) - 1: flags[idx+1] = 1
        elif word in "}":
            flags[idx] = 1
            if idx > 0: flags[idx-1] = 1
        elif word in "+-*/^=><|:":
            flags[idx] = 1
            if idx < len(raw_words) - 1: flags[idx+1] = 1
            if idx > 0: flags[idx-1] = 1
        elif re.match(r'\\[a-zA-Z]+', word):
            flags[idx] = 1

    for idx in range(len(flags)):
        if raw_words[idx] == '(':
            if idx < len(flags) - 1 and (flags[idx+1] or raw_words[idx+1] == '('):
                flags[idx] = True
        elif raw_words[idx] == ')':
            if idx > 0 and (flags[idx-1] or raw_words[idx-1] == ')'):
                flags[idx] = True


    p = re.compile('.+[<>=|].+')
    q = re.compile('^.+=$')

    curr_index = 0
    words = []
    curr_expression = ""
    statements = {}
    values = {}

    while curr_index < len(raw_words):
        word = raw_words[curr_index]
        if flags[curr_index] == 0:
            if curr_index > 0 and flags[curr_index-1] == 1:
                if p.match(curr_expression):
                    key = "@s_%d" % len(statements)
                    words.extend([key, "holds"])
                    statements[key] = curr_expression
                else:
                    key = "@v_%d" % len(values)
                    words.append(key)
                    values[key] = curr_expression
                curr_expression = ""
            words.append(word)
        else:
            curr_expression += word
        curr_index += 1
    if len(curr_expression) > 0:
        if p.match(curr_expression):
            key = "@s_%d" % len(statements)
            words.extend([key, "is", "true"])
            statements[key] = curr_expression
        elif q.match(curr_expression):
            key = "@s_%d" % len(statements)
            words.extend([key, 'is', 'true'])
            statements[key] = curr_expression + "\what"
        else:
            key = "@v_%d" % len(values)
            words.append(key)
            values[key] = curr_expression

    word_dict = dict(enumerate(words))
    return word_dict, statements, values

