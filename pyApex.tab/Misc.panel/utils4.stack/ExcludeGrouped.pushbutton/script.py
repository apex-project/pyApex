# -*- coding: utf-8 -*-
__title__ = 'Exclude Grouped'
__doc__ = """Exclude grouped elements from selection

Shift+Click - isolate grouped elements"""
__context__ = 'Selection'
__helpurl__ = "https://apex-project.github.io/pyApex/help#exclude-grouped"

from pyrevit import revit
selection = revit.get_selection()

def filter_grouped(e, inverse = False):
    if inverse:
        return e.GroupId.IntegerValue != -1
    else:
        return e.GroupId.IntegerValue == -1

if __name__ == '__main__':
    sel = selection.elements
    sel = list(filter(lambda e: filter_grouped(e, __shiftclick__), sel))
    selection.set_to(sel)
