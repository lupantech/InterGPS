import itertools
import requests
from geosolver import settings
import networkx as nx

__author__ = 'minjoon'

class SyntaxParse(object):
    def __init__(self, words, directed, undirected, rank, score):
        self.words = words
        self.directed = directed
        self.undirected = undirected
        self.rank = rank
        self.score = score

    def get_words(self, span):
        return tuple(self.words[idx] for idx in range(*span))

    def get_word(self, index):
        if index < 0:
            return None
        return self.words[index]

    def get_pos_by_index(self, index):
        if index not in self.undirected._node:
            return None
        tag = self.undirected._node[index]['tag']
        return tag

    def get_pos_by_span(self, span):
        """
        If the span is > 2 words, then obatin the tag of the latter word (higher plain index).
        Usually the compound is the former.
        """
        return self.get_pos_by_index(span[-1]-1)

    def iterate_spans(self, maxlen=2):
        for start in range(len(self.words)):
            for spanlen in range(maxlen):
                end = start + spanlen + 1
                if end <= len(self.words):
                    yield (start, end)

    def shortest_path_between_spans(self, s0, s1, directed=False):
        paths = [self.shortest_path_between_indices(i0, i1, directed)
                 for i0, i1 in itertools.product(range(*s0), range(*s1))]
        return min(paths, key=lambda path: len(path))

    def shortest_path_between_indices(self, i0, i1, directed=False):
        graph = self.undirected
        if directed:
            graph = self.directed
        path = nx.shortest_path(graph, i0, i1)
        return path

    def distance_between_spans(self, s0, s1, directed=False):
        distances = [self.distance_between_indices(i0, i1, directed)
                     for i0, i1 in itertools.product(range(*s0), range(*s1))]
        return min(distances)

    def plain_distance_between_spans(self, s0, s1, directed=False):
        distances = [self.plain_distance_between_indices(i0, i1, directed)
                     for i0, i1 in itertools.product(range(*s0), range(*s1))]
        return min(distances)

    def distance_between_indices(self, i0, i1, directed=False):
        graph = self.undirected
        if directed:
            graph = self.directed
        d = nx.shortest_path_length(graph, i0, i1)
        return d

    def plain_distance_between_indices(self, i0, i1, directed=False):
        if directed:
            return i1 - i0
        return abs(i1-i0)

    def relation_between_spans(self, s0, s1, directed=False):
        relations = [self.relation_between_indices(i0, i1, directed)
                     for i0, i1 in itertools.product(range(*s0), range(*s1))]
        for relation in relations:
            if relation is not None:
                return relation
        return None

    def relation_between_indices(self, i0, i1, directed=False):
        graph = self.undirected
        if directed: graph = self.directed

        if i1 in graph[i0]:
            label = graph[i0][i1]['label']
            return label
        return None

    def get_neighbors(self, span, directed=False):
        graph = self.undirected
        if directed: graph = self.directed

        nbrs = {}
        for from_ in range(*span):
            for to in graph[from_]:
                nbrs[to] = graph[from_][to]['label']
        return nbrs


class SyntaxParser(object):
    def get_syntax_parses(self, words, k, unique=True):
        """
        Returns a list of (tree, score) pair in order of decreasing score
        """
        raise Exception("This function must be overriden!")

    def get_best_syntax_parse(self, words, parser=True):
        return self.get_syntax_parses(words, 1, parser=parser)[0]


class StanfordDependencyParser(SyntaxParser):
    """
    Connects to stanford parser sever via http.
    """
    def __init__(self, server_url):
        self.server_url = server_url

    def get_syntax_parses(self, words, k, unique=True, parser=True):
        # FIXME : this should be fixed at geoserver level
        words = {key: word.lstrip().rstrip() for key, word in words.items()}
        if not parser:
            return [SyntaxParse(words, None, None, None, None)]

        sentence = [words[index] for index in sorted(words.keys())]
        neutral_sentence = [_neutralize(word) for word in sentence]
        params = {'words': '+'.join(neutral_sentence), 'k': k, 'paragraph': ' '.join(neutral_sentence)}
        r = requests.get(self.server_url, params=params)
        data = r.json()
        trees = []

        for rank, tree_data in enumerate(data):
            score = tree_data['score']
            tuples = tree_data['tuples']
            graph = nx.DiGraph()
            for label, from_, to, from_tag, to_tag in tuples:
                from_ -= 1
                to -= 1
                if from_ < 0:
                    continue
                graph.add_edge(from_, to, label=label)
                if 'label' not in graph._node[from_]:
                    graph._node[from_]['label'] = "%s-%d" % (words[from_], from_)
                    graph._node[from_]['word'] = words[from_]
                    graph._node[from_]['tag'] = from_tag

                if 'label' not in graph._node[to]:
                    graph._node[to]['label'] = "%s-%d" % (words[to], to)
                    graph._node[to]['word'] = words[to]
                    graph._node[to]['tag'] = to_tag

            if unique and not any(_match_trees(syntax_tree.directed, graph) for syntax_tree in trees):
                tree = SyntaxParse(words, graph, graph.to_undirected(), rank, score)
                trees.append(tree)

        return trees

def _neutralize(word):
    if word.startswith("@v"):
        return 'number'
    if word.startswith("@s"):
        return "statement"
    return word

def _match_trees(tree0, tree1, match_edge_label=False):
    """
    Returns True if tree0 and tree1 are identical.
    Edge labels are not considered unless match_edge_label is set to True.

    :param tree0:
    :param tree1:
    :param match_edge_label:
    :return:
    """
    assert isinstance(tree0, nx.DiGraph)
    assert isinstance(tree1, nx.DiGraph)
    for u, v, data in tree0.edges(data=True):
        if not tree1.has_edge(u, v):
            return False
        if match_edge_label and data['label'] != tree1[u][v]['label']:
            return False
    return True

stanford_parser = StanfordDependencyParser(settings.STANFORD_PARSER_SERVER_URL)
