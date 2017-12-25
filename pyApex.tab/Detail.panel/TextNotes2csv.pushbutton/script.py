# -*- coding: utf-8 -*-
__doc__ = """Export all textnotes content to csv.

Context: select views or sheets where you want to search for textnotes

Экспорт содержимого всех "Текстов" в csv-файл.

Контекст: выберите виды или листы, на которых необходимо найти тексты
"""
__title__ = 'TextNotes2csv'

__helpurl__ = "https://apex-project.github.io/pyApex/help#TextNotes2csv"

import csv
import os
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import *
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons


try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr
    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >= 4 and PYREVIT_VERSION.minor >= 5

if pyRevitNewer44:
    from pyrevit import script, revit
    from pyrevit.forms import SelectFromList, SelectFromCheckBoxes, pick_folder, pick_file, save_file
    output = script.get_output()
    logger = script.get_logger()
    from pyrevit.revit import doc, uidoc, selection
    selection = selection.get_selection()
    my_config = script.get_config()

else:
    from scriptutils import logger
    from scriptutils.userinput import WPFWindow, pick_folder, pick_file, save_file
    from revitutils import doc, uidoc, selection
    my_config = script.config


def get_views():
    selection = uidoc.Selection.GetElementIds()
    views_selected = filter(lambda e: doc.GetElement(e).GetType().IsSubclassOf(View), selection)

    if len(views_selected) == 0:
        error_text = "No views selected.\nTextnotes from all project views will be exported."

        q = TaskDialog.Show(__title__, error_text,
                            TaskDialogCommonButtons.Ok | TaskDialogCommonButtons.Cancel)

        if str(q) == "Cancel":
            return
        else:
            return None

    else:
        return views_selected


def extract_views_from_sheets(views):
    result = []
    for v in views:
        if type(view) == ViewSheet:
            result += v.GetAllPlacedViews()
        else:
            result.append(view)

    return result

#
# def views_from_sheet(view):
#     if type(view) == ViewSheet:
#         views = s.GetAllPlacedViews()
#     else:
#         views = [view]
#
#     return views


def get_textnotes(view_ids=None):
    collector = FilteredElementCollector(doc)  # collect elements visible on view
    elements = collector.OfClass(TextNote).ToElements()

    textnotes_dict = {}
    unique = []

    for e in elements:
        owner_view_id = e.OwnerViewId

        if view_ids and owner_view_id not in view_ids:
            continue

        if e.OwnerViewId not in textnotes_dict.keys():
            textnotes_dict[e.OwnerViewId] = []

        etext = e.Text.replace('\n', ' ').replace('\r', ' ')

        if etext not in unique:
            unique.append(etext)
            textnotes_dict[e.OwnerViewId].append((e.Id, etext))

    return textnotes_dict


def format_results(textnotes_dict):
    cl_sheets = FilteredElementCollector(doc)
    sheetsnotsorted = cl_sheets.OfCategory(BuiltInCategory.OST_Sheets).WhereElementIsNotElementType().ToElements()
    sheetsnotsorted = list(sheetsnotsorted)
    # Last empty element to check not placed views
    sheetsnotsorted.append(None)

    result = []

    # List of views which wasnt checked
    views_left = textnotes_dict.keys()

    for s in sheetsnotsorted:
        if s:
            sheet_views = [s.Id]
            sheet_id = s.Id
            sheet_name = s.Name
            sheet_views += s.GetAllPlacedViews()
        else:
            sheet_name = ""
            sheet_id = ""
            sheet_views = views_left

        # todo: search for use of .Parameter[] indexer.
        for v_id in sheet_views:
            if v_id in textnotes_dict:
                views_left.remove(v_id)

                v = doc.GetElement(v_id)

                tt = textnotes_dict[v_id]

                for t in tt:
                    result.append([sheet_name,sheet_id,
                                   v.Name,v_id,
                                   t[1],t[0]])

    return result

def write_csv(all_rows):
    default_filename = "textnotes_%s" % doc.Title

    try:
        init_dir = my_config.init_dir
        if not os.path.exists(init_dir):
            init_dir = ''
    except:
        init_dir = ''

    export_file = save_file(file_ext="csv", init_dir=init_dir, default_name=default_filename)

    print('%s\n\nWriting...' % export_file)

    with open(export_file, 'w') as f:
        writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        writer.writerow(['Sheet', 'SheetID', 'View', 'ViewID', 'Text', 'TextId'])
        writer.writerow([])

        for r in all_rows:
            row = []
            for v in r:
                try:
                    vv = v.ToString()
                except:
                    vv = str(v)
                row.append(vv)

            writer.writerow([unicode(s).encode("utf-8") for s in row])

    print('Completed')


def main():
    views_selected = get_views()

    if views_selected:
        print('%d views selected' % len(views_selected))

    textnotes_dict = get_textnotes(views_selected)
    result = format_results(textnotes_dict)
    write_csv(result)


if __name__ == "__main__":
    main()
