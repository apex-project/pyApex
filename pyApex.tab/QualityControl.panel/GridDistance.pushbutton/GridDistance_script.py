__title__ = "Grid Distance"
from pyrevit import script, revit

logger = script.get_logger()
output = script.get_output()
linkify = output.linkify
selection = revit.get_selection()
doc = revit.doc
uidoc = revit.uidoc

import clr
import math
import itertools
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
from Autodesk.Revit.DB import *
# from typing import List, Dict, Tuple

def get_grids(view_id=None, ids=False):
    """
    Collect all grids in current document

    :param view_id: filter by view
    :param ids: return ids or elements
    :return: list of ids or elements
    """
    if view_id:
        cl = FilteredElementCollector(doc, view_id)
    else:
        cl = FilteredElementCollector(doc)
    grids = cl.OfCategory(BuiltInCategory.OST_Grids).WhereElementIsNotElementType()
    if ids:
        return grids.ToElementIds()
    else:
        return grids.ToElements()


def curve_location(crv, base_curve):  # type: (Line, Line) -> XYZ
    crv.MakeUnbound()
    intersection_result_array = clr.Reference[IntersectionResultArray]()
    set_comparison_result = base_curve.Intersect(crv, intersection_result_array)
    if set_comparison_result != SetComparisonResult.Overlap:
        raise Exception("set_comparison_result != SetComparisonResult.Overlap: %s" %
                        str(set_comparison_result))
    for intersection_result in intersection_result_array.GetEnumerator():
        print(intersection_result)
        return intersection_result.XYZPoint


def curve_angle(crv, mode="deg", precision_max=5):
    pt_start = crv.GetEndPoint(0)
    pt_end = crv.GetEndPoint(1)
    x = abs(pt_start.X - pt_end.X)
    y = abs(pt_start.Y - pt_end.Y)
    if x == 0:
        rad = 0
    else:
        rad = math.atan(y / x)
    k = 1
    if pt_start.X < pt_end.X:
        k *= -1
    if pt_start.Y < pt_end.Y:
        k *= -1
    rad = rad * k

    if mode == "deg":
        return round(math.degrees(rad) % 90, precision_max)
    else:
        return round(rad % (math.pi / 2), precision_max + 3)


def split_angles_list(list_of_angles, precision=2):
    """
    Generator to split list of angles by group with certain precision

    :param list_of_angles: list of angles to group
    :param precision: precision in degrees. If the difference is larger than this value, it would be considered as a new group
    :return: a Generator which yields each group of angles as separated list
    """
    out = []  # temporary "container" with angles in current group
    # sort angles in given list
    list_of_angles = list(list_of_angles)
    list_of_angles.sort()
    # set first value as minimum value
    last_min_angle = list_of_angles[0]
    # iterate through each angle in sorted list
    for x in list_of_angles:
        # get difference between two angles
        # if the difference is larger than precision (by default >2 degrees)
        # that means a new group has begun
        if abs(x - last_min_angle) > precision:
            # yield list of angles in current group
            yield out
            # and erase temporary "container"
            out = []
            last_min_angle = x
        # add angle to a temporary "container"
        out.append(x)
    if len(out) > 0:
        yield out


curve_angles = {}
curve_distances = {}


def group_grids(grids, precision=2):
    """
    Group grids by angle

    :param grids: grids to group
    :param curve_angles: dictionary of 
    :param precision: precision (e.g. if 2 then 0.01 degrees difference would be considered as the same group
    :return: {angle : [grids]}
    """
    global curve_angles
    # FIXME check: there can be a failure, than many grids have the same angle.
    #  It is not correct to group them by angle
    #  But if they are already grouped that's okay ?
    groups_by_angle_no_round = {}  # dictionary (angle : [grid]s)
    groups_by_angle = {}  # each first angle in splited list [angle : [[grid]s]]

    for grid in grids:
        grid_angle = curve_angle(grid.Curve)
        curve_angles[grid.Id] = grid_angle

        if grid_angle not in groups_by_angle_no_round.keys():
            groups_by_angle_no_round[grid_angle] = []
        groups_by_angle_no_round[grid_angle].append(grid)

    grid_angles = list(groups_by_angle_no_round.keys())

    # split angles list with certain precision
    for angles_group in split_angles_list(grid_angles, precision):
        # check if first angle in a group already in a dictionary
        # (first angle is a leader of the group)
        if angles_group[0] not in groups_by_angle.keys():
            groups_by_angle[angles_group[0]] = []

        for k in angles_group:
            groups_by_angle[angles_group[0]] += groups_by_angle_no_round[k]
    logger.debug("groups_by_angle:")
    logger.debug(groups_by_angle)
    return groups_by_angle


def find_outlier_grids_distance(
        grids_grouped):  # type: (Dict[float, List[Grid]]) -> List[Tuple[List[ElementId],List[ElementId]]]
    """
    Get list of outliers (and orphaned) in certain format. If there are no outliers, list won't be mentioned
    :param grids_grouped: dictionary {angle: [grids]}
    :return: [([ids_good],[ids_bad]),...]
    """
    global curve_angles
    group_outliers = {}

    result = []

    for group_angle, group_grids in grids_grouped.items():
        if group_angle not in group_outliers.keys():
            group_outliers[group_angle] = {}

        # extend dictionary with grids by adding one more level
        # was: {group_angle: [grids]}
        # now: {group_angle: {grid_angle: grids}}
        for grid in group_grids:
            grid_angle = curve_angles[grid.Id]
            if grid_angle not in group_outliers[group_angle].keys():
                group_outliers[group_angle][grid_angle] = []
            group_outliers[group_angle][grid_angle].append(grid.Id)
        # if all grids in a group have the same angle - that's okay, skip it
        if len(group_outliers[group_angle].keys()) == 1:
            continue
        # Sort precise grid groups by length - how many grids in each of them
        # only group angles (keys) are stored
        angles_sorted = sorted(group_outliers[group_angle].keys(),
                               key=lambda x: len(group_outliers[group_angle][x]),
                               reverse=True)
        ids_good = [] # type : List[ElementId]
        ids_bad = [] # type : List[ElementId]
        # iterate through angles of sub groups
        for i in range(len(angles_sorted)):
            grid = angles_sorted[i]
            # put the largest sub group in GOOD results
            if i == 0 and len(group_outliers[group_angle][grid]) > 1:
                ids_good += group_outliers[group_angle][grid]
            # put all the others sub groups in BAD result
            #  (as well as orphaned - groups with only one grids inside)
            else:
                ids_bad += group_outliers[group_angle][grid]
        result.append((ids_good, ids_bad))
    return result


def get_design_options_ids(doc):
    """
    Get design options in a document

    :param doc: Document
    :return: dictionary of ids DesignOptionsSets and ids of DesignOptions
    """
    cl = FilteredElementCollector(doc)

    design_options = cl.OfClass(DesignOption).WhereElementIsNotElementType().ToElements()
    if len(design_options) == 0:
        return

    do_dict = {}
    for do in design_options:
        s_id = do.get_Parameter(BuiltInParameter.OPTION_SET_ID).AsElementId()
        if s_id not in do_dict.keys():
            do_dict[s_id] = []
        do_dict[s_id].append(do.Id)

    return do_dict


def element_design_option_equals(element, design_options_id):
    """
    Check if design option of certain element equals given design option
    or has no design option

    :param element: Element to check
    :param design_options_id: Design option id to compare
    :return: bool
    """
    do = element.get_Parameter(BuiltInParameter.DESIGN_OPTION_ID).AsElementId()
    return do == ElementId.InvalidElementId or do in design_options_id


def group_by_design_options(elements, design_options_dict):
    """
    Group elements of design options

    :param elements: Elements to group
    :param design_options_dict: Dictionary of DesignOptionSets and DesignOptions
    :return:
    """
    combinations = list(itertools.product(*list(design_options_dict.values())))
    result = []
    for c in combinations:
        els = filter(lambda e: element_design_option_equals(e, c), elements)
        result.append(list(els))
    return result


def run(interactive=False):
    """

    :param interactive: show dialogs
    :return: None
    """

    # Ask user to confirm running of the script
    if interactive:
        text = "Run Grid distance check?"
        a = TaskDialog.Show(__title__, text,
                            TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.Cancel)
        if str(a) != "Yes":
            return
    # Collect all grids in current document
    grids = get_grids()
    # Filter linear grids
    grids_linear = filter(lambda x: not x.IsCurved, grids)
    # Get list of design options in a document
    design_options_dict = get_design_options_ids(doc)
    # If there are design options in a document, group grids
    if design_options_dict:
        # list of lists of elements grouped by design options
        elements_by_design_option = group_by_design_options(grids_linear, design_options_dict)
    else:
        elements_by_design_option = [grids_linear, ]
    ids_bad_to_override = []  # list of false result
    ids_orphaned = []  # list of "outliers"

    for i in range(len(elements_by_design_option)):
        # if there are design options in a document, show combination index
        if len(elements_by_design_option) > 1:
            print("Design options combination %d" % (i + 1))
        # get list of grids in current design options combination
        grids_by_design_option = elements_by_design_option[i]
        logger.debug(grids_by_design_option)

        grids_grouped = group_grids(grids_by_design_option, precision=2)

        # get outliers
        outliers = find_outlier_grids_distance(grids_grouped)
        for outliers_pair in outliers:
            ids_good, ids_bad = outliers_pair
            if len(ids_bad) == 0:
                continue
            # add bad ids to mark them later
            ids_bad_to_override += ids_bad

            if len(ids_good) > 0:
                good_id = ids_good[0]
                print("Outliers from grid \"%s\" %s:" % (doc.GetElement(good_id).Name, \
                                                         linkify(good_id)))
            else:
                good_id = None
                print("Orphaned grids:")

            for g_id in ids_bad:
                g_name = doc.GetElement(g_id).Name
                if good_id:
                    print("\"%s\" ( %s&deg; ) %s " % (g_name, \
                                                      curve_angles[g_id] - curve_angles[good_id], linkify(g_id),))
                else:
                    print("\"%s\" %s " % (g_name, linkify(g_id),))

            print("\n\n")

    if type(doc.ActiveView) == ViewPlan and len(ids_bad_to_override) > 0:
        text = "Check completed\n%d errors found. Mark outliers grids on active plan view \"%s\"?" % (
            len(ids_bad_to_override), doc.ActiveView.Name)
        a = TaskDialog.Show(__title__, text,
                            TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No)

        if a == "No":
            return

        override_gray = OverrideGraphicSettings() \
            .SetProjectionLineColor(Color(200, 200, 200))

        override_red = OverrideGraphicSettings().SetProjectionLineColor(Color(255, 0, 0)) \
            .SetProjectionLineWeight(6)

        t = Transaction(doc)
        t.Start("Override graphics")

        for g in grids:
            doc.ActiveView.SetElementOverrides(g.Id, override_gray)

        grids_visible = get_grids(doc.ActiveView.Id, ids=True)

        for g in ids_bad_to_override:
            if g not in grids_visible:
                line = doc.Create.NewDetailCurve(doc.ActiveView, doc.GetElement(g).Curve)
                doc.ActiveView.SetElementOverrides(line.Id, override_red)
            doc.ActiveView.SetElementOverrides(g, override_red)

        t.Commit()

    if len(ids_bad_to_override) == 0:
        TaskDialog.Show(__title__, "Check completed\n0 errors")


def rotate_vector90(xyz):
    return XYZ(xyz.Y, -xyz.X, xyz.Z)


def rotate_curve(crv):
    if not isinstance(crv, Line):
        raise Exception("Crv is not a line")
    curve = crv.Clone()

    end_point = curve.GetEndPoint(0)
    curve.MakeUnbound()
    return Line.CreateUnbound(end_point, rotate_vector90(curve.Direction))


def test():
    pairs = [
        [458093, 754886],
        [458133, 754997],
        [755372, 755373]
    ]
    for p in pairs:
        curve_first = None
        last_point = None
        for e_id_int in p:
            print(e_id_int)
            e = doc.GetElement(ElementId(e_id_int))
            crv = e.Curve
            if not curve_first:
                curve_first = rotate_curve(crv)
            point = curve_location(crv, curve_first) # type : XYZ
            if last_point is None:
                last_point = point
            distance = point.DistanceTo(last_point)
            print(distance * 304.8)


if __name__ == '__main__':
    # test()
    run(interactive=True)
