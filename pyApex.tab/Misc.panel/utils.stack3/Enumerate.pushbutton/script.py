# -*- coding: utf-8 -*-
__title__ = 'Enumerate'
__doc__ = """"""

__helpurl__ = "https://apex-project.github.io/pyApex/help#enumerate"
__doc__ = 'Select many objects by IDs or error text'

import os.path
from pprint import pprint
import time

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ViewType
from Autodesk.Revit.UI import TaskDialog,TaskDialogCommonButtons
from Autodesk.Revit.DB import BuiltInCategory, ElementId, Definition, StorageType
from System.Collections.Generic import List
from Autodesk.Revit.DB import Transaction, TransactionGroup


try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr
    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >= 4 and PYREVIT_VERSION.minor >= 5

if pyRevitNewer44:
    from pyrevit import script, revit, forms
    from pyrevit.forms import WPFWindow

    logger = script.get_logger()
    from pyrevit.revit import doc, uidoc, selection
    selection = selection.get_selection()

else:
    forms = None
    from scriptutils import logger
    from scriptutils import this_script as script
    from scriptutils.userinput import WPFWindow
    from revitutils import doc, uidoc, selection


# uidoc = __revit__.ActiveUIDocument
# doc = __revit__.ActiveUIDocument.Document
# doc_info = doc.ProjectInformation
# ppath = doc.PathName
# pfilename = os.path.splitext(os.path.split(ppath)[1])[0]
#
# dir_path = os.path.dirname(os.path.realpath(__file__))
#
# print os.path.dirname(os.path.realpath(__file__))
#
# uidoc = __revit__.ActiveUIDocument
# doc = __revit__.ActiveUIDocument.Document
#
# selIds = uidoc.Selection.GetElementIds()
# sheets = []
# for eId in selIds:
#     sheets.append(doc.GetElement(eId))
#
# t = Transaction(doc, "Sheets enum")
# t.Start()
# for v in sheets:
#     part = 0
#
#     for p in v.GetParameters("INF_Sheet number"):
#         if p.AsString():
#             shn = p.AsString()
#
#     if shn:
#         for p in v.GetParameters("Номер листа"):
#             if p.AsString() and p.IsReadOnly==False:
#                 p.Set("AS-CNCP л." + str(shn))
#
#     print shn
#
# t.Commit()


def get_selection():
    """
    Get selected objects / sheets / views or allows user to select

    :return: selected objects or None
    """
    return selection.elements


# def filter_selection_geometry(selection, leave_geom):
#     """
#     Filter selection to leave only preferable type
#
#     :param selection: list of elements
#     :param leave_geom: bool - leave only geometry or only views, sheets etc.
#     :return: filtered list of elements
#     """
#     result = []
#     for e in selection:
#         if leave_geom:
#
#         else:
#


class EnumerateWindow(WPFWindow):
    def __init__(self, xaml_file_name, selected_elements):
        is_geom_list, not_geom_list = self.separate_geometry(selected_elements)
        sel_filtered, self.is_geom = self.filter_geometry_and_other(is_geom_list, not_geom_list)

        if not sel_filtered:
            logger.error("Selection error or wrong elements were selected")
            return

        parameters_dict = self.get_selection_parameters(sel_filtered)

        self.parameters_sortable = self.filter_sortable(sel_filtered, parameters_dict)
        self.parameters_editable = self.filter_editable(parameters_dict)

        WPFWindow.__init__(self, xaml_file_name)
        self._set_comboboxes()

    def run(self):
        pass


    def _set_comboboxes(self):
        sortable_keys = self.parameters_sortable.keys()

        if self.is_geom:
            sortable_keys += [
                "---",
                "<Along curve>",
                "<X coordinate>",
                "<Y coordinate>",
                "<Z coordinate>"
            ]

        self.parameterToSort.ItemsSource = sortable_keys
        self.parameterToSet.ItemsSource = self.parameters_editable.keys()

    def separate_geometry(self, selection):
        """
        Check is most of elements have
        :param selection: list of elements
        :return: [[list of geometry], [list of other elements]]
        """
        is_geom = []
        not_geom = []

        for e in selection:
            if e.Location:
                is_geom.append(e)
            else:
                not_geom.append(e)

        return is_geom, not_geom


    def filter_geometry_and_other(self, is_geom, not_geom):
        elements = None
        is_geom_bool = None

        if not_geom and is_geom:
            errors_string = "Selection has %d geometry objects and %d other objects.\n" % (len(is_geom), len(not_geom),)

            if len(is_geom) > len(is_geom):
                q = TaskDialog.Show(__title__, errors_string + "Only geometry will be used.",
                                    TaskDialogCommonButtons.Ok | TaskDialogCommonButtons.Cancel)
                elements = is_geom
                is_geom_bool = True
            else:
                q = TaskDialog.Show(__title__, errors_string + "Only not-geometry elements will be used.",
                                    TaskDialogCommonButtons.Ok | TaskDialogCommonButtons.Cancel)
                elements = not_geom
                is_geom_bool = False
            if str(q) == "Cancel":
                return
        elif not_geom or is_geom:
            elements = is_geom if is_geom else not_geom
            is_geom_bool = True if is_geom else False

        return elements, is_geom_bool


    def get_selection_parameters(self, elements):
        """
        Get parameters which are common for all selected elements

        :param elements: Elements list
        :return: dict - {parameter_name: Parameter}
        """
        result = {}
        all_parameter_set = set()
        all_parameter_ids_by_element = {}

        # find all ids
        for e in elements:
            for p in e.Parameters:
                p_id = p.Definition.Id
                all_parameter_set.add(p)

                if e.Id not in all_parameter_ids_by_element.keys():
                    all_parameter_ids_by_element[e.Id] = set()
                all_parameter_ids_by_element[e.Id].add(p_id)

        # filter
        for p in all_parameter_set:
            p_id = p.Definition.Id
            exists_for_all_elements = True
            for e_id, e_params in all_parameter_ids_by_element.items():
                if p_id not in e_params:
                    exists_for_all_elements = False
                    break

            if exists_for_all_elements:
                result[p.Definition.Name] = p

        return result


    def filter_sortable(self, elements, parameters):
        """
        Filter parameters which has value for at least some of elements

        :param elements: list of elements
        :param parameters: list of parameters
        :return: filtered list of parameters
        """
        result = {}
        for p_name, p in parameters.items():
            for e in elements:
                param = e.get_Parameter(p.Definition)
                if param.HasValue:
                    result[p_name] = p
                    break
        return result


    def filter_editable(self, parameters):
        """
        Filter parameters which can be modified by users

        :param parameters: list of parameters
        :return: filtered list of parameters
        """
        ignore_types = [StorageType.ElementId, ]
        result = {n: p for n, p in parameters.iteritems()
                  if not p.IsReadOnly
                  and p.StorageType not in ignore_types}
        return result


def main():
    # Input
    sel = get_selection()
    if not sel:
        logger.error("Nothing selected")
        return

    if len(sel) < 2:
        logger.error('At least 2 elements or views must be selected.')
        return

    EnumerateWindow('window.xaml', sel).ShowDialog()


    #
    # print(parameters_sortable.keys())
    # print(parameters_editable.keys())
    # for n, p in parameters_editable.items():
    #     print(n, p.StorageType)
    # Let user to set options

    # filter editable
    # generate form
    # get user settings

    # Sort

    # Update parameters


if __name__ == "__main__":
    main()
    # e = selection.elements[0]
    # print()
    # for p in e.Parameters:
    #     print(p.Definition.Name, p.StorageType, p.UserModifiable, p.HasValue, p.AsValueString())
    #     print("\n")
