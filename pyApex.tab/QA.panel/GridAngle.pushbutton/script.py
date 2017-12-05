# -*- coding: utf-8 -*-

__doc__ = 'Check angles between grids'
__title__ = 'Grid Angles'
import os.path
from pprint import pprint
import time
import math

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, \
    BuiltInParameter, ElementId, ViewType,
    ViewPlanType, ViewPlan, ViewFamilyType, ViewFamily, DesignOption, Color, \
    OverrideGraphicSettings

from Autodesk.Revit.DB import Transaction, TransactionGroup

import os
from scriptutils import this_script

from scriptutils import logger
from scriptutils.userinput import CommandSwitchWindow

# def addtoclipboard(text):
#     command = 'echo ' + text.strip() + '| clip'
#     os.system(command)

#неясно, как реализовать выбор параметра-родителя тэга (tag.Door, tag.Room и т.д.)
uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

def get_grids():
    cl = FilteredElementCollector(doc)

    grids = cl.OfCategory(BuiltInCategory.OST_Grids).WhereElementIsNotElementType().ToElements()
    logger.debug(str(len(grids)) + " grids found")
    grids = filter(lambda x: not x.IsCurved, grids)

    return grids


def get_first_level():
    cl = FilteredElementCollector(doc)
    levels = cl.OfCategory(BuiltInCategory.OST_Levels).WhereElementIsNotElementType().ToElements()
    if(len(levels) > 0):
        return levels[0]

def floorplan_id():
    cl = FilteredElementCollector(doc);
    viewFamilyTypes = cl.OfClass(ViewFamilyType).ToElements();
    for e in viewFamilyTypes:
        if e and e.ViewFamily == ViewFamily.FloorPlan:
            return e.Id

def round_angle(a, t=0.00001):
    return int(a/t) * t

def curve_angle(crv, mode="deg", round=0.00001):
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
        return round_angle(math.degrees(rad), round) % 90
    else:
        return round_angle(rad, round/100) % (math.pi / 2)


def group_runs(li,tolerance=2):
    out = []
    li = list(li)
    li.sort()
    last_min = li[0]
    for x in li:
        if abs(x-last_min) > tolerance:
            yield out
            out = []
            last_min = x

        out.append(x)

    yield out

curve_angles = {}

override_gray = OverrideGraphicSettings()
override_gray.SetProjectionLineColor(Color(200,200,200))

override_red = OverrideGraphicSettings()
override_red.SetProjectionLineColor(Color(255,0,0))
override_red.SetProjectionLineWeight(6)
def group_grids(grids, tolerance = 2):
    groups_no_round = {}
    groups = {}
    t = Transaction(doc)
    t.Start("Reset graphics override")
    for g in grids:
        doc.ActiveView.SetElementOverrides(g.Id, override_gray)
        d = curve_angle(g.Curve)
        curve_angles[g.Id] = d

        if d not in groups_no_round.keys():
            groups_no_round[d] = []
        groups_no_round[d].append(g)
    t.Commit()
    keys = list(groups_no_round.keys())

    keys_groups = list(group_runs(keys, tolerance))

    for kg in keys_groups:
        if kg[0] not in groups.keys():
            groups[kg[0]] = []
        for k in kg:
            groups[kg[0]] += groups_no_round[k]

    return groups



def find_outliers(d):
    counts = {}
    for k,vv in d.items():

        if k not in counts.keys():
            counts[k] = {}

        for v in vv:
            d = curve_angles[v.Id]
            if d not in counts[k].keys():
                counts[k][d] = []
            counts[k][d].append(v.Id)

        if len(counts[k].keys()) == 1:
            continue

        angles_sorted = sorted(counts[k].keys(),
                               key=lambda x: len(counts[k][x]),
                               reverse=True)
        ids_good = []
        ids_bad = []
        for i in range(len(angles_sorted)):
            v = angles_sorted[i]
            if i == 0 and len(counts[k][v]) > 1:
                ids_good += counts[k][v]
            else:
                ids_bad += counts[k][v]

        print("\n%s" % k)

        print("Good ids:")

        t = Transaction(doc)
        t.Start("Override graphics")

        print( ", ".join(map(this_script.output.linkify, ids_good) ))


        print("\nBad ids:")
        print(", ".join( map(this_script.output.linkify, ids_bad) ))

        for g in ids_bad:
            doc.ActiveView.SetElementOverrides(g, override_red)
        print("\n")
        t.Commit()

def iterate_design_options():
    cl = FilteredElementCollector(doc)

    elements = cl.OfClass(DesignOption).WhereElementIsNotElementType().ToElements()
    t = Transaction(doc)

    for do in elements:
        t.Start("create views")
        floorView = ViewPlan.Create(doc, floorplan_id(), get_first_level().Id)
        floorView.Name = "01_GridAngles_%s" % do.Name

        t.Commit()
        t.Start("create do")
        p_do = floorView.get_Parameter(BuiltInParameter.DESIGN_OPTION_ID).Set(do.Id)
        t.Commit()

grids = get_grids()
# iterate_design_options()
find_outliers(group_grids(grids,5))

# else:
#   TaskDialog.Show(__title__,"Ошибка при выборе категории")
