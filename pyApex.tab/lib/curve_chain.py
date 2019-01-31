import itertools
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

    # chain
    selection_list_sorted = _find_curve_chain(selected_curve)
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
    return map(lambda x: doc.GetElement(x), result_ids)


def _find_curve_chain(curve):
    result = _sort_joined_curves_run(curve, 0)
    logger.info("Result 1")
    logger.info(map(lambda x: x.Id.IntegerValue, result))

    # another direction
    result_2 = _sort_joined_curves_run(curve, 1)

    logger.info("Result 2")
    logger.info(map(lambda x: x.Id.IntegerValue, result_2))
    if len(result_2) > 1:
        result_2 = list(reversed(result_2))[:-1]
        result = list(itertools.chain(result_2, result))

    logger.info("Result 3")
    logger.info(map(lambda x: x.Id.IntegerValue, result))
    return result


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