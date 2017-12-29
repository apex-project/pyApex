# -*- coding: utf-8 -*-

exceptions = [
    "Levels",
    "Work Plane Grid",
    "Viewports",
    "Other",
]

limit = 50
#
# def _filter_list(l):
#     l = filter(lambda x: len(x) > 0, l)
#     l = map(lambda x: x.strip("\n").strip("\n").strip("\r"), l)
#     return l
#
#
# def exceptions2str(l):
#     """"""
#
#     """back compatibility START"""
#     if type(l) != list:
#         l = exceptions2list(l)
#     """back compatibility END"""
#
#     l = _filter_list(l)
#     return "\n".join(l)
#
#
# def exceptions2list(s):
#     l = s.split("\n")
#
#     """back compatibility START"""
#     # remove empty rows
#     l = _filter_list(l)
#     # check is separator is ',' - not '\n'
#     if len(l) == 1:
#         if l[0].indexOf(",") != -1:
#             l = l[0].split(",")
#             l = filter(lambda x: len(x) > 0, l)
#     """back compatibility END"""
#
#     l = _filter_list(l)
#
#     return l
