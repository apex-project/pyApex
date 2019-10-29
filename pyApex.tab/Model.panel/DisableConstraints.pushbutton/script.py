# -*- coding: utf-8 -*-
__title__ = 'Disable\nConstraints'

__doc__ = """Disable all Constraints in the project (all locked dimensions). 
Shift+Click - recover from previous run"""

__helpurl__ = "https://apex-project.github.io/pyApex/help#disable-constraints"

from Autodesk.Revit.DB import BuiltInCategory, ElementId, JoinGeometryUtils, Transaction, FilteredElementCollector
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, TaskDialogResult,TaskDialogCommandLinkId
from pyrevit import script
from pyrevit.revit import doc, selection
import pickle
import os

selection = selection.get_selection()
append_mode = True

def get_datafile(reverse):
    global append_mode
    datafile = script.get_document_data_file("pyApex_Constraints", "pym")
    saved_list = []

    if os.path.exists(datafile):
        if reverse == False:
            td = TaskDialog("Constraints")
            td.MainInstruction = "File with elements saved after previous run found.\nHow to deal with it?"
            td.AddCommandLink(TaskDialogCommandLinkId.CommandLink1, "Remove it and replace")
            td.AddCommandLink(TaskDialogCommandLinkId.CommandLink2, "Append new data")
            td.AllowCancellation = True
            taskDialogResult = td.Show()
            if taskDialogResult == TaskDialogResult.Cancel:
                return None, None
            elif taskDialogResult == TaskDialogResult.CommandLink1:
                append_mode = False
            else:
                append_mode = True

        if append_mode:
            f = open(datafile, 'r')
            saved_list = pickle.load(f)
            f.close()

    # remove duplicates
    ids = list(set(saved_list))
    return datafile, ids


def save(datafile, ids):
    # remove duplicates
    ids = list(set(ids))
    # write
    f = open(datafile, 'w')
    pickle.dump(ids, f)
    f.close()


def IsGrouped(element):
    return element.GroupId.IntegerValue != -1


def process(datafile, saved_list=[], reverse=False):

    if not reverse:
        cl = FilteredElementCollector(doc).WhereElementIsNotElementType().OfCategory(BuiltInCategory.OST_Constraints)
        constraints = cl.ToElements()
        constraints_to_change = filter(lambda c: c.NumberOfSegments == 0, constraints)
        constraints_to_change = list(filter(lambda c: c.IsLocked, constraints_to_change))

        constraints_grouped = list(filter(lambda c: IsGrouped(c), constraints_to_change))
        constraints_to_change = list(filter(lambda c: not IsGrouped(c), constraints_to_change))
        
        td_text = "%d enabled Constraints found. Disable them?" % len(constraints_to_change)

        if (len(constraints_grouped) > 0):
            td_text += ("\n(%d Constraints are in groups, they will not be affected)" % len(constraints_grouped))
    else:

        td_text = "Reverse mode.\n%d saved Constraints found. Recover them?" % len(saved_list)
        constraints_to_change = []
        for id_int in saved_list:
            try:
                element = doc.GetElement(ElementId(id_int))
                constraints_to_change.append(element)
            except:
                pass

    tdres = TaskDialog.Show("Constraints", td_text,
                            TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No)

    if tdres == TaskDialogResult.No:
        return

    t = Transaction(doc, __title__)
    t.Start()
    is_error = False
    try:
        for constraint in constraints_to_change:
            constraint.IsLocked = True if reverse else False
            if not reverse:
                saved_list.append(constraint.Id.IntegerValue)

    except Exception as exc:
        is_error = True
        t.RollBack()
        TaskDialog.Show(__title__, "Error. Changes cancelled.")
    else:
        t.Commit()
        result_text = "Finished."
        if not reverse:
            result_text += "\nChanged elements saved. To recover then run the same script with SHIFT button"
        TaskDialog.Show(__title__,result_text)

    if not is_error:
        save(datafile, saved_list)
    # filter not existing
    selection.set_to([e.Id for e in constraints_to_change if e.IsValidObject])


def main():
    if __shiftclick__:
        reverse = True
    else:
        reverse = False
    datafile, saved_list = get_datafile(reverse)

    if not datafile:
        TaskDialog.Show(__title__, "Cancelled")
        return

    process(datafile, saved_list, reverse)


if __name__ == '__main__':
    main()
