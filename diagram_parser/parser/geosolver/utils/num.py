"""
Numerical utils
"""

__author__ = 'minjoon'


def round_vector(vector):
    return tuple(int(round(x)) for x in vector)


def dimension_wise_non_maximum_suppression(vectors, radii, dimension_wise_distances):
    """
    Performs dimension-wise non maximum suppression.
    vectors is a list of n-dimensional vectors (lists), and
    radii is an n-dimensional vector indicating the radius for each dimension.
    dimension_wise_distances is a function returning distance vector between two vectors.
    Ex. Euclidean dimension-wise distance between (1,2) and (4,1) is (3,1).

    :param vectors:
    :param radii:
    :return:
    """
    out_vectors = []
    if len(vectors) == 0:
        return out_vectors
    assert len(vectors[0]) == len(radii)

    for vector in vectors:
        cond = True
        for vector2 in out_vectors:
            distance_vector = dimension_wise_distances(vector, vector2)
            if all(x <= radii[i] for i, x in enumerate(distance_vector)):
                cond = False
                break

        if cond:
            out_vectors.append(vector)

    return out_vectors


def is_number(string):
    try:
        float(string)
        return True
    except:
        return False