# -*- coding: utf-8 -*- 
__doc__ = 'List elements dependent of selected level\nYou can select plan view to check its level'
import csv
import os
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import *
uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document



selection = uidoc.Selection.GetElementIds()

ignore_types = [Level,SunAndShadowSettings,Viewport,SketchPlane, Sketch]
if len(selection) == 0:
    print('Please, select level')
else:
    
    for s_id in selection:
        e = doc.GetElement(s_id)
        if type(e) == ViewPlan:
            e = e.GenLevel
        elif type(e) == Level:
            pass
        else:
            continue
        t = Transaction(doc, "Check level " + e.Name)
        t.Start()
        elements = doc.Delete(s_id)
        t.RollBack()
        element_ids = []
        print(e.Name)
        for edid in elements:
            ed = doc.GetElement(edid)
            if not ed:
                continue
            if type(ed) in ignore_types:
                continue
            element_ids.append(str(edid.IntegerValue))
            print("\t%d - %s" % (edid.IntegerValue, ed.GetType(), ))
        print("\n\t"  + ",".join(element_ids))
        print("\n\n")

