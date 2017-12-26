# -*- coding: utf-8 -*-
__title__ = 'Enumerate'
__doc__ = """"""

__helpurl__ = "https://apex-project.github.io/pyApex/help#enumerate"
__doc__ = 'Select many objects by IDs or error text'

import os.path
from pprint import pprint

import operator

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ViewType
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
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
    from pyrevit import script, revit
    from pyrevit.forms import WPFWindow

    logger = script.get_logger()
    from pyrevit.revit import doc, uidoc, selection

    selection = selection.get_selection()
    my_config = script.get_config()
else:
    forms = None
    from scriptutils import logger
    from scriptutils import this_script as script
    from scriptutils.userinput import WPFWindow
    from revitutils import doc, uidoc, selection

    my_config = script.config


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
        self.selection, self.is_geom = self.filter_geometry_and_other(is_geom_list, not_geom_list)

        self.extra_geom_keys = [
                                # "<Along curve>",
                                "<X coordinate>",
                                "<Y coordinate>",
                                "<Z coordinate>"
                                ]

        if not self.selection:
            logger.error("Selection error or wrong elements were selected")
            return

        parameters_dict = self.get_selection_parameters(self.selection)

        self.parameters_sortable = self.filter_sortable(self.selection, parameters_dict)
        self.parameters_editable = self.filter_editable(parameters_dict)

        WPFWindow.__init__(self, xaml_file_name)
        self._set_comboboxes()
        self.read_config()

    def read_config(self):
        try:
            self.textFormat.Text = str(my_config.text_format)
        except:
            self.textFormat.Text = my_config.text_format = "%s"

        try:
            self.leadingZeros.Text = str(my_config.leading_zeros)
        except:
            self.leadingZeros.Text = my_config.leading_zeros = "0"

        try:
            self.startFrom.Text = str(my_config.start_from)
        except:
            self.startFrom.Text = my_config.start_from = "1"

        try:
            self.parameterToSort.Text = str(my_config.parameter_to_sort)
        except:
            self.parameterToSort.Text = my_config.parameter_to_sort = ""

        try:
            self.parameterToSort.Text = str(my_config.parameter_to_sort)
        except:
            self.parameterToSort.Text = my_config.parameter_to_sort = ""

        try:
            self.parameterToSet.Text = str(my_config.parameter_to_set)
        except:
            self.parameterToSet.Text = my_config.parameter_to_set = ""

        try:
            self.isReversed.IsChecked = my_config.is_reversed
        except:
            self.isReversed.IsChecked = my_config.is_reversed = False
        script.save_config()

    def write_config(self):
        my_config.text_format = self.textFormat.Text
        my_config.leading_zeros = self.leadingZeros.Text
        my_config.parameter_to_sort = self.parameterToSort.Text
        my_config.parameter_to_sort = self.parameterToSort.Text
        my_config.parameter_to_set = self.parameterToSet.Text
        my_config.is_reversed = self.isReversed.IsChecked
        script.save_config()

    @property
    def parameter_to_sort(self):
        p = self.parameterToSort.Text
        if type(p) == str and p in self.extra_geom_keys:
            return p
        else:
            return self.parameters_sortable[p]

    @property
    def parameter_to_set(self):
        p = self.parameters_editable[self.parameterToSet.Text]
        return p

    @property
    def text_format(self):
        t = self.textFormat.Text.strip()
        if len(t) == 0:
            return

        if "%s" not in t:
            t += " %s"

        return t

    @property
    def leading_zeros(self):
        try:
            n = int(self.leadingZeros.Text)
        except:
            n = 0
        return n

    @property
    def start_from(self):
        return int(self.startFrom.Text)

    @property
    def is_reversed(self):
        return self.isReversed.IsChecked

    def run(self, sender, args):
        result = self.sort(self.selection, self.parameter_to_sort, self.is_reversed)
        i = self.start_from
        text_format = self.text_format
        zeros = self.leading_zeros

        t = Transaction(doc, __title__)
        t.Start()
        for r in result:
            e = r[0]
            definition = self.parameter_to_set.Definition
            param = e.get_Parameter(definition)
            if zeros:
                _i = str(i).zfill(zeros)
            else:
                _i = str(i)
            self.parameter_value_set(param, _i, text_format)
            i += 1
        t.Commit()

        my_config.start_from = i
        script.save_config()

        self.write_config()

    def sort(self, elements, parameter_to_sort, reverse=False):
        param_dict = self.element_parameter_dict(elements, parameter_to_sort)
        param_dict_sorted = sorted(param_dict.items(), key=operator.itemgetter(1), reverse=reverse)
        return param_dict_sorted
        # return map(lambda x: x[0], param_dict_sorted)

    def element_parameter_dict(self, elements, parameter_to_sort):
        result = {}
        for e in elements:
            if type(parameter_to_sort) == str:
                if parameter_to_sort[0] == "<" and parameter_to_sort[2:] == " coordinate>":
                    parameter_loc = parameter_to_sort[1]
                    loc = e.Location
                    v = getattr(loc.Point, parameter_loc)
                else:
                    logger.error("Parameter error")
                    return
            else:
                param = e.get_Parameter(parameter_to_sort.Definition)
                v = self.parameter_value_get(param)
            if v:
                result[e] = v

        return result

    def parameter_value_get(self, parameter):
        if not parameter.HasValue:
            return

        if parameter.StorageType == StorageType.Double:
            x = float(parameter.AsDouble())
        elif parameter.StorageType == StorageType.Integer:
            x = int(parameter.AsInteger())
        else:
            try:
                x = float(parameter.AsString().strip().replace(",", "."))
            except:
                x = parameter.AsString()
        return x

    def parameter_value_set(self, parameter, value, text_format):
        if parameter.StorageType == StorageType.Double or parameter.StorageType == StorageType.Integer:
            if text_format:
                try:
                    value = str(float(text_format % value))
                except:
                    pass
            parameter.SetValueString(value)
        else:
            if text_format:
                parameter.Set(text_format % value)
            else:
                parameter.Set(value)

    def _set_comboboxes(self):
        sortable_keys = self.parameters_sortable.keys()

        if self.is_geom:
            sortable_keys += ["---"]
            sortable_keys += self.extra_geom_keys

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

    def NumberValidationTextBox(self, sender, e):
        try:
            x = int(e.Text.strip())
            e.Handled = False
            return x

        except:
            e.Handled = True


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
