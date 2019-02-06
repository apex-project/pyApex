# -*- coding: utf-8 -*-
import itertools
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
from pyrevit import script, revit, forms
import pyapex_utils as pyu

logger = script.get_logger()


def pick_chain(doc):
    selection = revit.selection.get_selection()
    # last_selection = selection.element_ids
    selected_curve = revit.pick_element("Select curves to sort by")

    if not selected_curve:
        forms.alert("Nothing selected")
        return None, None

    logger.debug("selected_curve: %s" % str(selected_curve.Id))

    try:
        selected_curve.GeometryCurve
    except:
        forms.alert("Error! Selected element is not a Curve.\nOr it have no GeometryCurve parameter")
        return None, None

    if not selected_curve.GeometryCurve.IsBound:
        forms.alert("Error! Curve cannot be bounded")

    # chain
    selection_list_sorted, selection_list_sorted_isreversed = _find_curve_chain(selected_curve, doc)
    logger.debug("selection_list_sorted: %s" % selection_list_sorted)
    if len(selection_list_sorted) > 1:
        # TODO undo
        selection.set_to(selection_list_sorted)
        form_result = TaskDialog.Show("Select curve chain?", "Curve chain found. Use it?\nIf not, only one selected curve will be used",
                                      TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No)

        # selection.set_to(last_selection)
        if str(form_result) == "Yes":
            return selection_list_sorted, selection_list_sorted_isreversed
    logger.debug("Selected_curve: %s" % [selected_curve.Id])
    return [selected_curve.Id], None


def _sort_joined_curves_run(curve, doc, end=0):
    logger.debug("_sort_joined_curves_run, end: %d", end)
    curves = [curve]
    result = []
    result_ids = []
    result_reversed = []
    i = 0

    while len(curves) > 0 and i < 100:
        _end = end
        c = curves[0].GeometryCurve
        # unbound
        c_id = curves[0].Id
        logger.debug("%d %d %d" % (i, end, c_id.IntegerValue))

        if c_id not in result_ids:

            if len(result) != 0:
                c_last = result[-1]
                logger.debug("%s=%s" % (c_last.GetEndPoint(end), c.GetEndPoint(end)))
                bool_points_equal = pyu.compare_xyz(c_last.GetEndPoint(end), c.GetEndPoint(end), 5)
            else:
                bool_points_equal = False
            logger.debug("eq %s" % bool_points_equal)
            if bool_points_equal:
                logger.debug("Reverse")
                # c = c.CreateReversed()
                result_reversed.append(True)
                _end = not end
            else:
                result_reversed.append(False)
            result_ids.append(c_id)
            result.append(c)
        else:
            break
        curves = map(lambda x: doc.GetElement(x), doc.GetElement(c_id).GetAdjoinedCurveElements(_end))
        i += 1

    result_curves = []
    for i in range(len(result_ids)):
        c_id = result_ids[i]
        c = doc.GetElement(c_id).GeometryCurve
        if result_reversed[i]:
            logger.debug("reversed")
            c = c.CreateReversed()
        result_curves.append(c)
    return result_ids, result_reversed


def _find_curve_chain(curve, doc):
    result, result_is_reversed = _sort_joined_curves_run(curve, doc, 1)

    result_2, result_is_reversed_2 = _sort_joined_curves_run(curve, doc, 0)

    # combine result
    if len(result_2) > 1:
        result_2 = list(reversed(result_2))[:-1]
        result_is_reversed_2 = list(reversed(result_is_reversed_2))[:-1]
        result = list(itertools.chain(result_2, result))
        result_is_reversed = list(itertools.chain(result_is_reversed_2, result_is_reversed))

    return result, result_is_reversed


def chain_closest_point(point, chain, chain_is_reversed, doc):
    smallest_distance = None
    param = None
    for i in range(len(chain)):
        logger.debug(i)
        c = doc.GetElement(chain[i])
        c_geom = c.GeometryCurve
        int_res = c_geom.Project(point)
        _param = c_geom.ComputeNormalizedParameter(int_res.Parameter)

        if chain_is_reversed:
            logger.debug("i: %d, Distance: %f, param: %f, reversed: %s" % (i, int_res.Distance, _param, chain_is_reversed[i]))
            if chain_is_reversed[i]:
                _param = 1.0 - _param
                logger.debug("param: %f" % _param)
        else:
            logger.debug(
                "i: %d, Distance: %f, param: %f, reversed: -" % (i, int_res.Distance, _param))
        if smallest_distance is None or smallest_distance > int_res.Distance:
            # or (i == len(chain) - 1:
            smallest_distance = int_res.Distance
            param = i + _param

    return param
