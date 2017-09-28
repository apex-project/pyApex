# -*- coding: utf-8 -*- 
'Changes all materials appearance to Phase - New. Useful for paper-like render.\nShift-Click: config exceptions'
__title__ = 'White Materials'

my_config = this_script.config

import csv
import os
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import *
from datetime import datetime
import re

data_dir = "D:\\"
white_material_name = "Phase - New"
ignore_names = ["ENSCAPE","wood","Fabric Sails","Metal Roofing","Светильник","Concrete Screed"]


uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
doc_title = doc.Title
data_full_path = os.path.join(data_dir, doc_title + ".tmp")
_new_path, ext = os.path.splitext(data_full_path)
new_path = _new_path + datetime.now().strftime("_%y%m%d_%H-%M-%S") + ext



def change_materials(reverse=False, limit=None):
    mat_dict = {}
    mat_list = []
    if reverse == True:
        if os.path.exists(data_full_path):
            with open(data_full_path, "r") as f:
                lines = f.readlines()
            for l in lines:
                m_id, a_id = l.split(",")
                mat_dict[m_id] = a_id

        else:
            print("%s not exists" % data_full_path)
            return
    else:
        if os.path.exists(data_full_path):
            print("%s already exists, it will be renamed" % data_full_path)


            try:
                os.rename(data_full_path, new_path)
            except Exception as e:
                print("Error renaming\n" + str(e))
                return

    selection = uidoc.Selection.GetElementIds()

    cl = FilteredElementCollector(doc)
    mats = list(cl.OfCategory(BuiltInCategory.OST_Materials).WhereElementIsNotElementType().ToElements())

    try:
        white_mat = filter(lambda x: x.Name == white_material_name, mats)[0]
    except Exception as e:
        print("Material '%s' not found" % white_material_name)
        print(e)
        return

    white_mat_a = white_mat.AppearanceAssetId

    print("White material: %s\nAssetId: %d" % (white_material_name, white_mat_a.IntegerValue))

    t = Transaction(doc, "Change materials to Phase - New")
    t.Start()

    if limit>0:
        mats = mats[:limit]
    for m in mats:
        m_name = m.Name
        m_name_ignore = False
        for r in ignore_names:
            re_match = re.match(r, m_name, re.I)
            if re_match:
                m_name_ignore = True
                break

        if m_name_ignore:
            print("%s - ignore name" % m_name)
            continue

        if m.Transparency != 0:
            print("%s - ignore transparency" % m_name)
            continue

        m_id = m.Id
        a_id = m.AppearanceAssetId

        if reverse == False:
            mat_list.append("%d,%d" % (m_id.IntegerValue, a_id.IntegerValue,))
            m.AppearanceAssetId = white_mat_a
            print("%s (%d - %d) changed to white" % (m_name, m_id.IntegerValue, a_id.IntegerValue))
        else:
            _id = int(mat_dict[str(m_id.IntegerValue)])
            m.AppearanceAssetId = ElementId(_id)

            print("%s (%d) changed to %d" % (m_name, m_id.IntegerValue, _id))

    t.Commit()
    if reverse == False:
        with open(data_full_path, "w") as f:
            for item in mat_list:
                f.write("%s\n" % item)
    else:
        try:
            os.rename(data_full_path, new_path)
        except Exception as e:
            print("Error renaming\n" + str(e))
            # for e_id in selection:
            #     e = doc.GetElement(e_id)
            #     p = e.GetOrderedParameters()
            #     print(p)


def main():
    if __forceddebugmode__:
        limit = 10
        print("limit %d" % limit)
    else:
        limit = None
    if __shiftclick__:
        change_materials(True, limit=limit)
    else:
        change_materials(limit=limit)


main()
