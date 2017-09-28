# -*- coding: utf-8 -*- 
__doc__ = 'Unjoin selected elements'

from scriptutils import logger
import os
import re
import os.path as op
import pickle as pl
import clr

from Autodesk.Revit.DB import BuiltInCategory, ElementId, JoinGeometryUtils, Transaction

from System.Collections.Generic import List
from Autodesk.Revit.UI import TaskDialog,TaskDialogCommonButtons

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
selection = uidoc.Selection.GetElementIds()

rng = range(len(selection))
checked_pairs = []
joined_pairs = []
c = 0

for x in rng:
    for y in rng:
        if x == y:
            continue
        _p = sorted([x,y])
        _t = (_p[0],_p[1])
        if _t in checked_pairs:
            continue

        checked_pairs.append(_t)
        eid1 = selection[_p[0]]
        eid2 = selection[_p[1]]
        e1,e2 = doc.GetElement(eid1),doc.GetElement(eid2)
        joined = JoinGeometryUtils.AreElementsJoined(doc,e1,e2)
        if joined:
            joined_pairs.append((e1,e2))

if len(joined_pairs) > 0:
    t = Transaction(doc)
    t.Start("UnjoinSelected")
    for p in joined_pairs:
        JoinGeometryUtils.UnjoinGeometry(doc,p[0],p[1])
        c+=1
    t.Commit()
TaskDialog.Show("R","%d пар элементов разъединены" % c)


