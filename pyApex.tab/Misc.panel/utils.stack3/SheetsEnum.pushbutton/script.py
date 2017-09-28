# -*- coding: utf-8 -*- 
"""
Copyright (c) 2014-2016 Ehsan Iran-Nejad
Python scripts for Autodesk Revit

This file is part of pyRevit repository at https://github.com/eirannejad/pyRevit

pyRevit is a free set of scripts for Autodesk Revit: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 3, as published by
the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

See this link for a copy of the GNU General Public License protecting this package.
https://github.com/eirannejad/pyRevit/blob/master/LICENSE
"""
#Autodesk.Revit.DB.View
__doc__ = 'Select many objects by IDs or error text'
commit_prefix = "selectManyByIds.py "
import os.path
from pprint import pprint
import time


from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ViewType
from Autodesk.Revit.UI import TaskDialog,TaskDialogCommonButtons
from Autodesk.Revit.DB import BuiltInCategory, ElementId
from System.Collections.Generic import List
from Autodesk.Revit.DB import Transaction, TransactionGroup

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
doc_info = doc.ProjectInformation
ppath = doc.PathName
pfilename = os.path.splitext(os.path.split(ppath)[1])[0]

dir_path = os.path.dirname(os.path.realpath(__file__))
#dir_path = os.path.dirname(ppath)


print os.path.dirname(os.path.realpath(__file__))
import os

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

cl_sheets = FilteredElementCollector(doc)
allsheets = cl_sheets.OfCategory(BuiltInCategory.OST_Sheets)
sheets = filter(lambda x: (str(x.GetType()) == 'Autodesk.Revit.DB.ViewSheet' and not x.IsTemplate), # and not x.IsTemplate
                   allsheets)
selIds = uidoc.Selection.GetElementIds()
sheets = []
for eId in selIds:
    sheets.append(doc.GetElement(eId))

t = Transaction(doc, "Toggle views parameters")
t.Start()
for v in sheets:
    print "v"
    part = 0
    # for p in v.GetParameters("INF_Album"):
    #     if p.AsString():
    #         if p.AsString()[:5]=="AS-CNCP":
    #             part = 1
    # shn = 0
    # if part == 1:
    for p in v.GetParameters("INF_Sheet number"):
        if p.AsString():
            shn = p.AsString()

    if shn:
        for p in v.GetParameters("Номер листа"):
            if p.AsString() and p.IsReadOnly==False:
                p.Set("AS-CNCP л." + str(shn))
                # print p.AsString() + " > л." + str(shn)
    print shn
print "commin"
t.Commit()