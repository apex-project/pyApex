# -*- coding: utf-8 -*- 
__doc__ = 'List all text notes on placed views\nto csv D:\\textnotes...'
import csv
import os
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import *
uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

# cl_sheets = FilteredElementCollector(doc)
# sheetsnotsorted = cl_sheets.OfCategory(BuiltInCategory.OST_Sheets).WhereElementIsNotElementType().ToElements()
# # print(len(sheetsnotsorted))
# sheets = sorted(sheetsnotsorted, key=lambda x: x.SheetNumber)

# collector = FilteredElementCollector(doc) #collect elements visible on view
# elements = collector.OfClass(TextNote).ToElements()
# textnotes_dict = {}
# unique = []

# for e in elements:
#     if e.OwnerViewId not in textnotes_dict.keys():
#         textnotes_dict[e.OwnerViewId] = []
#     etext = e.Text.replace('\n',' ').replace('\r',' ')
#     if etext not in unique:
#         unique.append(etext)
#         textnotes_dict[e.OwnerViewId].append((e.Id,etext))

# all_rows = []

selection = uidoc.Selection.GetElementIds()
# sheets = filter(lambda e: type(doc.GetElement(e)) == ViewSheet, selection)
# test = doc.GetElement(selection[0])
# print(type(test))
ignore_types = [Level,SunAndShadowSettings,Viewport,SketchPlane, Sketch]
if len(selection) == 0:
    print('Please, select level')
else:

    for s_id in selection:
        e = doc.GetElement(s_id)

        if type(e) != Level:
            continue
        t = Transaction(doc, "Check level " + e.Name)
        t.Start()
        elements = doc.Delete(s_id)
        t.RollBack()
        element_ids = []
        for edid in elements:
            ed = doc.GetElement(edid)
            if not ed:
                continue
            if type(ed) in ignore_types:
                continue
            element_ids.append(str(edid.IntegerValue))
            print(edid.IntegerValue, ed.GetType())
        print(",".join(element_ids))

