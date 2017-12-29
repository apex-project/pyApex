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
