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
    # try:
    last_selection = selection.element_ids
    selected_curve = revit.pick_element("Select curves to sort by")

    if not selected_curve:
        forms.alert("Nothing selected")
        return None, None

    logger.info("selected_curve: %s" % str(selected_curve.Id))

    try:
        _geom_curve = selected_curve.GeometryCurve
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

    # except Exception as exc:
    #     logger.error(exc)
    #     pass


# def closest_point(chain, point):
#     parameter_sum = 0
#     for c in chain:


def _hashset_to_list(hset):
    return list(map(lambda x: x, hset))


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

    # while len(curves) > 0 and i < 100:
    #     c = curves[0]
    #     logger.info("%d %d %d" % (i, _end, c.Id.IntegerValue))
    #     if c.Id not in result_ids:
    #         result_ids.append(c.Id)
    #         result.append(c)
    #         # direction_changed = False
    #     else:
    #         break
    #         # if direction_changed:
    #         #     break
    #         # else:
    #         #     _end = int(not(_end))
    #         #     direction_changed = True
    #         #     continue
    #
    #     curves = map(lambda x: doc.GetElement(x), c.GetAdjoinedCurveElements(_end))
    #     logger.info(map(lambda x: x.Id.IntegerValue, curves))
    #     #
    #     # # on the first iteration check if something in another direction
    #     # if i == 0 and len(curves) == 0: #  and _end == end
    #     #     logger.info("i == 0 and len(curves) == 0 and end == 0")
    #     #     _end = not(_end)
    #     #     curves = map(lambda x: doc.GetElement(x), c.GetAdjoinedCurveElements(_end))
    #
    #     curves = _hashset_to_list(curves)
    #     if len(curves) > 0:
    #         new_end_point_a = curves[0].GeometryCurve.GetEndPoint(_end)
    #         new_end_point_b = curves[0].GeometryCurve.GetEndPoint(int(not _end))
    #
    #         if pyu.compare_xyz(new_end_point_a, last_end_point):
    #             # curves = map(lambda x: doc.GetElement(x), c.GetAdjoinedCurveElements(int(not _end)))
    #             # curves = _hashset_to_list(curves)
    #             last_end_point = curves[0].GeometryCurve.GetEndPoint(int(not _end))
    #             _end = not _end
    #         else:
    #             last_end_point = curves[0].GeometryCurve.GetEndPoint(_end)
    #
    #     #         logger.info("%s = %s" % (new_end_point0.ToString(), last_end_point0.ToString()))
    #     #         logger.info("or %s = %s" % (new_end_point1.ToString(), last_end_point1.ToString()))
    #     #         _end = int(not _end)
    #     #         # logger.info("pyu.compare_xyz(new_end_point, last_end_point)")
    #     #         # curves = map(lambda x: doc.GetElement(x), c.GetAdjoinedCurveElements(int(not _end)))
    #     #         last_end_point0 = _curves[0].GeometryCurve.GetEndPoint(1)
    #     #         last_end_point1 = _curves[0].GeometryCurve.GetEndPoint(0)
    #     #     else:
    #     #         last_end_point0 = new_end_point0
    #     #         last_end_point1 = new_end_point1

        # curves = _hashset_to_list(curves)

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
    # return map(lambda x: doc.GetElement(x), result_ids)


def _find_curve_chain(curve):
    result, result_is_reversed = _sort_joined_curves_run(curve, 1)
    logger.info("Result 1")
    # logger.info(map(lambda x: x.Id.IntegerValue, result))

    # another direction
    result_2, result_is_reversed_2 = _sort_joined_curves_run(curve, 0)

    logger.info("Result 2")
    # logger.info(map(lambda x: x.Id.IntegerValue, result_2))
    if len(result_2) > 1:
        result_2 = list(reversed(result_2))[:-1]
        result_is_reversed_2 = list(reversed(result_is_reversed_2))[:-1]
        result = list(itertools.chain(result_2, result))
        result_is_reversed = list(itertools.chain(result_is_reversed_2, result_is_reversed))

    logger.info("Result 3")
    # logger.info(map(lambda x: x.Id.IntegerValue, result))
    return result, result_is_reversed


def _normalise_chain_direction(chain):
    chain = list(map(lambda x: x.GeometryCurve, chain))
    if len(chain) <= 1:
        return chain
    print(len(chain))
    result = []
    for i in range(len(chain)):
        was_reversed = False
        if i == 0:
            # fix direction for first curve
            if pyu.compare_xyz(chain[i].GetEndPoint(0), chain[i+1].GetEndPoint(1)) \
                    or pyu.compare_xyz(chain[i].GetEndPoint(0), chain[i+1].GetEndPoint(0)):
                chain[i] = chain[i].CreateReversed()
                was_reversed = True
        else:
            # fix current curve
            if pyu.compare_xyz(chain[i-1].GetEndPoint(1), chain[i].GetEndPoint(1)):
                chain[i] = chain[i].CreateReversed()
                was_reversed = True
        result.append(was_reversed)

    print("result")
    print(result)
    return chain


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

