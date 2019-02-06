# -*- coding: utf-8 -*-
import itertools
from Autodesk.Revit.DB import ElementId, Curve
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
from pyrevit import script, revit, forms
import pyapex_utils as pyu

output = script.get_output()
logger = script.get_logger()
linkify = output.linkify
doc = revit.doc
uidoc = revit.uidoc
selection = revit.get_selection()


def pick_chain(find_chain=False):
    last_selection = selection.element_ids
    selected_curve = revit.pick_element("Select curves to sort by")

    if not selected_curve:
        forms.alert("Nothing selected")
        return None, None

    logger.info("selected_curve: %s" % str(selected_curve.Id))

    try:
        selected_curve.GeometryCurve
    except:
        forms.alert("Selected element is not a Curve.\nOr it have no GeometryCurve parameter")
        return None, None
    # chain
    selection_list_sorted, selection_list_sorted_isreversed = _find_curve_chain(selected_curve)
    logger.info("selection_list_sorted: %s" % selection_list_sorted)
    if len(selection_list_sorted) > 1 and find_chain:
        # TODO undo
        selection.set_to(selection_list_sorted)
        form_result = TaskDialog.Show("Select curve chain?", "Curve chain found. Use it?\nIf not, only one selected curve will be used",
                                      TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No)

        selection.set_to(last_selection)
        if str(form_result) == "Yes":
            return selection_list_sorted, selection_list_sorted_isreversed
    logger.info("Sselected_curve: %s" % [selected_curve.Id])
    return [selected_curve.Id], None


def _sort_joined_curves_run(curve, end=0):
    curves = [curve]
    result = []
    result_ids = []
    result_reversed = []
    i = 0

    while len(curves) > 0 and i < 100:
        _end = end
        c = curves[0].GeometryCurve
        c_id = curves[0].Id
        logger.info("%d %d %d" % (i, end, c_id.IntegerValue))

        if c_id not in result_ids:

            if len(result) != 0:
                c_last = result[-1]
                logger.info("%s=%s" % (c_last.GetEndPoint(end), c.GetEndPoint(end)))
                bool_points_equal = pyu.compare_xyz(c_last.GetEndPoint(end), c.GetEndPoint(end))
            else:
                bool_points_equal = False
            logger.info("eq %s" % bool_points_equal)
            if bool_points_equal:
                logger.info("Reverse")
                c = c.CreateReversed()
                result_reversed.append(True)
                _end = not end
            else:
                result_reversed.append(False)
            result_ids.append(c_id)
            result.append(c)
        else:
            break

        curves = map(lambda x: doc.GetElement(x),
                     doc.GetElement(c_id).GetAdjoinedCurveElements(_end))

        i += 1
    print(result_reversed)
    result_curves = []
    for i in range(len(result_ids)):
        c_id = result_ids[i]
        c = doc.GetElement(c_id).GeometryCurve
        if result_reversed[i]:
            logger.info("reversed")
            c = c.CreateReversed()
        result_curves.append(c)
    return result_ids, result_reversed


def _find_curve_chain(curve):
    result, result_is_reversed = _sort_joined_curves_run(curve, 1)
    result_2, result_is_reversed_2 = _sort_joined_curves_run(curve, 0)

    # combine result
    if len(result_2) > 1:
        result_2 = list(reversed(result_2))[:-1]
        result_is_reversed_2 = list(reversed(result_is_reversed_2))[:-1]
        result = list(itertools.chain(result_2, result))
        result_is_reversed = list(itertools.chain(result_is_reversed_2, result_is_reversed))

    return result, result_is_reversed


def chain_closest_point(point, chain, chain_is_reversed):
    smallest_distance = None
    param = None
    for i in range(len(chain)):
        logger.info(i)
        c = doc.GetElement(chain[i])
        int_res = c.GeometryCurve.Project(point)
        _param = c.GeometryCurve.ComputeNormalizedParameter(int_res.Parameter)

        if chain_is_reversed:
            logger.info("i: %d, Distance: %f, param: %f, reversed: %s" % (i, int_res.Distance, _param, chain_is_reversed[i]))
            if chain_is_reversed[i]:
                _param = 1.0 - _param
                logger.info("param: %f" % _param)
        else:
            logger.info(
                "i: %d, Distance: %f, param: %f, reversed: -" % (i, int_res.Distance, _param))
        if smallest_distance is None \
                or smallest_distance > int_res.Distance \
                or i == len(chain) - 1:
            smallest_distance = int_res.Distance
            param = i + _param

    return param

lines, lines_is_reversed = pick_chain(True)
if lines:
    logger.info("lines, lines_is_reversed")
    logger.info(lines)
    p = chain_closest_point(doc.GetElement(ElementId(5169)).Location.Point, lines, lines_is_reversed)
    print(p)

