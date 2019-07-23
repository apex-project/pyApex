# -*- coding: utf-8 -*-
def filter_list(l):
    l = filter(lambda x: len(x) > 0, l)
    l = map(lambda x: x.strip("\n").strip("\n").strip("\r"), l)
    return l


def list2str(l):
    """"""

    """back compatibility START"""
    if type(l) != list:
        l = str2list(l)
    """back compatibility END"""

    l = filter_list(l)
    return "\n".join(l)


def str2list(s):
    l = s.split("\n")

    """back compatibility START"""
    # remove empty rows
    l = filter_list(l)
    # check is separator is ',' - not '\n'
    if len(l) == 1:
        if "," in l[0]:
            l = l[0].split(",")
            l = filter(lambda x: len(x) > 0, l)
    """back compatibility END"""

    l = filter_list(l)

    return l


def compare_xyz(xyz1, xyz2, precision = None):
    if precision != None:
        return round(xyz1.X, precision) == round(xyz2.X, precision) \
               and round(xyz1.Y, precision) == round(xyz2.Y, precision) \
               and round(xyz1.Z, precision) == round(xyz2.Z, precision)
    else:
        return xyz1.X == xyz2.X and xyz1.Y == xyz2.Y and xyz1.Z == xyz2.Z

def is_ascii(s):
    return all(ord(c) < 128 for c in s)

def almost_equal(x, y, rnd=10):
    return round(x*(10^rnd)) == round(y*(10^rnd))