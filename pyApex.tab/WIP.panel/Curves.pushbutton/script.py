# -*- coding: utf-8 -*-
import itertools
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
from pyrevit import script, revit, forms
output = script.get_output()
logger = script.get_logger()
linkify = output.linkify
doc = revit.doc
uidoc = revit.uidoc
selection = revit.get_selection()
from curve_chain import pick_chain, _normalise_chain_direction

def pick_line(find_chain = False):
    # try:
    last_selection = selection.element_ids
    selected_curve = revit.pick_element("Select curves to sort by")

    # chain
    selection_list_sorted = find_curve_chain(selected_curve)
    if len(selection_list_sorted) > 0 and find_chain:
        selection.set_to(selection_list_sorted)
        form_result = TaskDialog.Show("Select curve chain?", "Curve chain found. Use it?",
                            TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No)

        selection.set_to(last_selection)
        if str(form_result) == "Yes":
            return selection_list_sorted


    return [selected_curve]
    # except Exception as exc:
    #     logger.error(exc)
    #     pass


def hashset_to_list(hset):
    return list(map(lambda x: x, hset))


def sort_joined_curves_run(curve, end = 0):
    curves = [curve]
    result = []
    i = 0
    while len(curves) > 0 and i < 100:
        e_id = curves[0]
        logger.info(i)
        logger.info(e_id)
        result.append(e_id)
        c = doc.GetElement(e_id)
        curves = c.GetAdjoinedCurveElements(end)
        # on the first iteration check if something in another direction
        if i == 0 and len(curves) == 0 and end == 0:
            end = 1
            curves = c.GetAdjoinedCurveElements(end)
        curves = hashset_to_list(curves)
        i += 1
    return result

def find_curve_chain(curve):
    result = sort_joined_curves_run(curve.Id, 0)

    # another direction
    result_2 = sort_joined_curves_run(curve.Id, 1)
    logger.info(result_2)
    if len(result_2) > 1:
        result_2 = list(reversed(result_2))[:-1]
        result = itertools.chain(result_2, result)

    result = list(map(lambda c_id: doc.GetElement(c_id), result))
    return result


lines = pick_chain(True)
# print("_normalise_chain_direction")
# print(_normalise_chain_direction(lines))

