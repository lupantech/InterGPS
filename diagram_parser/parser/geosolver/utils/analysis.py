import matplotlib.pyplot as plt

__author__ = 'minjoon'

def draw_pr(triple_dict):
    """
    {threshold: [ref, ret, mat]}

    :param triple_dict:
    :return:
    """
    ts = sorted(triple_dict.keys())
    ps = [float(triple_dict[th][2])/max(1,triple_dict[th][1]) for th in ts]
    rs = [float(triple_dict[th][2])/max(1,triple_dict[th][0]) for th in ts]
    plt.plot(ts, ps)
    plt.plot(ts, rs)
    plt.show()
