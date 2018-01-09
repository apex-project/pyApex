# -*- coding: utf-8 -*-

__doc__ = 'Check angles between grids'
__title__ = 'Grid Angles'
try:
    from pyrevit.versionmgr import PYREVIT_VERSION
    pyRevitNewer44 = PYREVIT_VERSION.major >=4 and PYREVIT_VERSION.minor >=5
except:
    from pyrevit import versionmgr
    PYREVIT_VERSION = versionmgr.get_pyrevit_version()
    pyRevitNewer44 = True


import math
import itertools
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import *

if pyRevitNewer44:
    from pyrevit import script, revit, DB, UI
    logger = script.get_logger()
    output = script.get_output()
    linkify = output.linkify
    selection = revit.get_selection()
    doc = revit.doc
    uidoc = revit.uidoc

else:
    from scriptutils import logger
    from Autodesk.Revit import DB, UI
    from scriptutils import this_script
    linkify = this_script.output.linkify
    uidoc = __revit__.ActiveUIDocument
    doc = uidoc.Document


def get_grids(view_id = None, ids=False):
    if view_id:
        cl = FilteredElementCollector(doc, view_id)
    else:
        cl = FilteredElementCollector(doc)
    grids = cl.OfCategory(BuiltInCategory.OST_Grids).WhereElementIsNotElementType()

    if ids:
        return grids.ToElementIds()
    else:
        return grids.ToElements()


def curve_angle(crv, mode="deg", precision_max=5):
    pt_start = crv.GetEndPoint(0)
    pt_end = crv.GetEndPoint(1)
    x = abs(pt_start.X - pt_end.X)
    y = abs(pt_start.Y - pt_end.Y)
    if x==0:
        rad = 0
    else:
        rad = math.atan(y/x)
    k = 1
    if pt_start.X < pt_end.X:
        k *= -1
    if pt_start.Y < pt_end.Y:
        k *= -1
    rad = rad * k

    if mode == "deg":
        return round(math.degrees(rad) % 90, precision_max)
    else:
        return round(rad % (math.pi / 2), precision_max+3)


def group_runs(li,precision=2):
    out = []
    li = list(li)
    li.sort()
    last_min = li[0]
    for x in li:
        if abs(x-last_min) > precision:
            yield out
            out = []
            last_min = x

        out.append(x)

    yield out

curve_angles = {}


def group_grids(grids, precision = 2):
    groups_no_round = {}
    groups = {}

    for g in grids:
        d = curve_angle(g.Curve)
        curve_angles[g.Id] = d

        if d not in groups_no_round.keys():
            groups_no_round[d] = []
        groups_no_round[d].append(g)

    keys = list(groups_no_round.keys())

    keys_groups = list(group_runs(keys, precision))

    for kg in keys_groups:
        if kg[0] not in groups.keys():
            groups[kg[0]] = []
        for k in kg:
            groups[kg[0]] += groups_no_round[k]

    return groups


def find_outlier_grids(grids_grouped):
    group_outliers = {}

    result = []

    for k,vv in grids_grouped.items():

        if k not in group_outliers.keys():
            group_outliers[k] = {}

        for v in vv:
            d = curve_angles[v.Id]
            if d not in group_outliers[k].keys():
                group_outliers[k][d] = []
            group_outliers[k][d].append(v.Id)

        if len(group_outliers[k].keys()) == 1:
            continue

        # Sort precise grid groups by length - how many grids in each of them
        angles_sorted = sorted(group_outliers[k].keys(),
                               key=lambda x: len(group_outliers[k][x]),
                               reverse=True)
        ids_good = []
        ids_bad = []

        for i in range(len(angles_sorted)):
            v = angles_sorted[i]

            if i == 0 and len(group_outliers[k][v]) > 1:
                ids_good += group_outliers[k][v]
            else:
                ids_bad += group_outliers[k][v]


        result.append([ids_good,ids_bad])

    return result


def get_design_options(doc):
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


def check_element_designoption(element, design_options):
    do = element.get_Parameter(BuiltInParameter.DESIGN_OPTION_ID).AsElementId()

    return do == ElementId(-1) or do in design_options


def group_by_design_options(elements, design_options_dict):
    combinations = list(itertools.product(*list(design_options_dict.values())))

    result = []
    for c in combinations:
        els = filter(lambda e: check_element_designoption(e,c), elements)
        result.append(list(els))

    return result


def run(interactive=False):
    if interactive:
        text = "Сейчас будет выполнена проверка осей"
        a = TaskDialog.Show(__title__, text,
            TaskDialogCommonButtons.Yes|TaskDialogCommonButtons.Cancel)

        if str(a) != "Yes":
            return

        # if type(doc.ActiveView) == ViewPlan:
        #     text += "\n\nПерекрасить ошибочные оси на текущем плане \"%s\"?"

    grids = get_grids()
    grids_linear = filter(lambda x: not x.IsCurved, grids)

    design_options_dict = get_design_options(doc)

    if design_options_dict:
        elements_by_do = group_by_design_options(grids_linear, design_options_dict)
    else:
        elements_by_do = [grids_linear,]

    ids_bad_to_override = []
    ids_orphaned = []

    for i in range(len(elements_by_do)):
        if len(elements_by_do) > 1:
            print("Design options combination %d" % (i + 1))
        grids_do = elements_by_do[i]
        grids_grouped = group_grids(grids_do, precision = 2)

        outliers = find_outlier_grids(grids_grouped)

        for grids_group in outliers:
            if len(grids_group) != 2:
                continue
            ids_good, ids_bad = grids_group

            if len(ids_bad) == 0:
                continue
            ids_bad_to_override += ids_bad

            if len(ids_good) > 0:
                good_id = ids_good[0]
                print("Outliers from grid \"%s\" %s:" % ( doc.GetElement(good_id).Name, \
                                                    linkify(good_id) ) )
            else:
                good_id = None
                print("Orphaned grids:" )

            for g_id in ids_bad:
                g_name = doc.GetElement(g_id).Name
                if good_id:
                    print("\"%s\" ( %s&deg; ) %s " % (g_name, \
                                            curve_angles[g_id] - curve_angles[good_id], linkify(g_id), ) )
                else:
                    print("\"%s\" %s " % (g_name, linkify(g_id), ) )

            print("\n\n")

    if type(doc.ActiveView) == ViewPlan and len(ids_bad_to_override) > 0:
        text = "Check completed\n%d errors found. Mark outliers grids on active plan view \"%s\"?" %(len(ids_bad_to_override), doc.ActiveView.Name)
        a = TaskDialog.Show(__title__, text,
            TaskDialogCommonButtons.Yes|TaskDialogCommonButtons.No)

        if a == "No":
            return

        override_gray = OverrideGraphicSettings() \
            .SetProjectionLineColor(Color(200,200,200))

        override_red = OverrideGraphicSettings().SetProjectionLineColor(Color(255,0,0)) \
            .SetProjectionLineWeight(6)


        t = Transaction(doc)
        t.Start("Override graphics")

        for g in grids:
            doc.ActiveView.SetElementOverrides(g.Id, override_gray)

        grids_visible = get_grids(doc.ActiveView.Id, ids=True)

        for g in ids_bad_to_override:
            if g not in grids_visible:
                line = doc.Create.NewDetailCurve(doc.ActiveView, doc.GetElement(g).Curve )
                doc.ActiveView.SetElementOverrides(line.Id, override_red)
            doc.ActiveView.SetElementOverrides(g, override_red)

        t.Commit()

    if len(ids_bad_to_override) == 0:
        TaskDialog.Show(__title__, "Check completed\n0 errors")

run(interactive=True)
