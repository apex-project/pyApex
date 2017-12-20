# -*- coding: utf-8 -*-
__doc__ = 'List all text notes on placed views\nto csv D:\\textnotes...'
import csv
import os
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import *
from scriptutils.userinput import WPFWindow, pick_folder


uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

cl_sheets = FilteredElementCollector(doc)
sheetsnotsorted = cl_sheets.OfCategory(BuiltInCategory.OST_Sheets).WhereElementIsNotElementType().ToElements()
# print(len(sheetsnotsorted))
sheets = sorted(sheetsnotsorted, key=lambda x: x.SheetNumber)

collector = FilteredElementCollector(doc) #collect elements visible on view
elements = collector.OfClass(TextNote).ToElements()
textnotes_dict = {}
unique = []

for e in elements:
    if e.OwnerViewId not in textnotes_dict.keys():
        textnotes_dict[e.OwnerViewId] = []
    etext = e.Text.replace('\n',' ').replace('\r',' ')
    if etext not in unique:
        unique.append(etext)
        textnotes_dict[e.OwnerViewId].append((e.Id,etext))

all_rows = []

selection = uidoc.Selection.GetElementIds()
sheets = filter(lambda e: type(doc.GetElement(e)) == ViewSheet, selection)
# test = doc.GetElement(selection[0])
# print(type(test))
if len(sheets) == 0:
    print('Please, select sheets')
else:
    print('%d sheets selected' % len(sheets))
    for s_id in selection:
        # todo: search for use of .Parameter[] indexer.
        # print(s.Name)
        s = doc.GetElement(s_id)
        sheet_name = s.Name
        views = s.GetAllPlacedViews()

        for v_id in views:
            v = doc.GetElement(v_id)

            if v_id in textnotes_dict:
                tt = textnotes_dict[v_id]
                for t in tt:
                    all_rows.append([sheet_name,s.Id,v.Name,v_id,t[1],t[0]])

            # collector = FilteredElementCollector(doc,v_id) #collect elements visible on view
            # elements = collector.OfClass(TextNote).ToElements()
            # # print(v.Name)
            # for e in elements:
            #     # print(e.Text,e.Id)
            #     if e.Text not in unique:
            #         unique.append(e.Text)

        # break
        # print('{2} NUMBER: {0}   NAME:{1}'.format(name.rjust(10),
        #                                       s.LookupParameter('Имя листа').AsString().ljust(50),
        #                                       s.Id.ToString()
        #                                       ))

    doc_info = doc.ProjectInformation
    ppath = doc.PathName
    pfilename = os.path.splitext(os.path.split(ppath)[1])[0]

    csvfile = 'D:\\textnotes_%s.csv' % pfilename
    print('%s\n\nWriting...' % csvfile)


    with open(csvfile, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=';',quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        writer.writerow(['Sheet','SheetID','View','ViewID','Text','TextId'])
        writer.writerow([])
        for r in all_rows:
            row = []
            for v in r:
                # print(v)
                # try:

                #     vv = v
                #     'encoding error'
                # except:
                # print(v)
                try:
                    vv = v.ToString()
                except:
                    vv = str(v)
                row.append(vv)
            # print(row)
            writer.writerow([unicode(s).encode("utf-8") for s in row])

    print('all done')
