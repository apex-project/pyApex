# -*- coding: utf-8 -*-
__title__ = 'Copy parameter'
__doc__ = """Set value of one parameter to another one. Works with selected element or elements.

Записывает значение одного параметра в другой параметр выбранного элемента(ов)."""

__helpurl__ = "https://apex-project.github.io/pyApex/help#copy-paramter"

from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
from Autodesk.Revit.DB import BuiltInCategory, ElementId, Definition, StorageType

from Autodesk.Revit.DB import Transaction, TransactionGroup

try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr

    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >= 4 and PYREVIT_VERSION.minor >= 5

if pyRevitNewer44:
    from pyrevit import script
    from pyrevit.forms import WPFWindow, SelectFromList

    logger = script.get_logger()
    from pyrevit.revit import doc, selection

    selection = selection.get_selection()
    my_config = script.get_config()
else:
    forms = None
    from scriptutils import logger
    from scriptutils import this_script as script
    from scriptutils.userinput import WPFWindow, SelectFromList
    from revitutils import doc, selection

    my_config = script.config


class CheckBoxParameter:
    def __init__(self, parameter, default_state=False):
        self.parameter = parameter
        self.name = parameter.Definition.Name
        self.state = default_state

    def __str__(self):
        return self.name

    def __nonzero__(self):
        return self.state

    def __bool__(self):
        return self.state


class CopyParameterWindow(WPFWindow):
    def __init__(self, xaml_file_name, selected_elements):
        self.selection = selected_elements
        if not self.selection:
            TaskDialog.Show(__title__, "Selection is empty")
            return

        self.parameters_dict = self.get_selection_parameters(self.selection)
        self.parameters_editable = self.filter_editable(self.parameters_dict)
        WPFWindow.__init__(self, xaml_file_name)
        self._set_comboboxes()
        self.read_config()

    def read_config(self):
        # check are last parameters available
        try:
            if my_config.parameter_to_get not in self.parameters:
                my_config.parameter_to_get = ""
        except:
            pass
        try:
            if my_config.parameter_to_set not in self.parameters_editable:
                my_config.parameter_to_set = ""
        except:
            pass

        try:
            self.parameterToGet.Text = str(my_config.parameter_to_get)
        except:
            self.parameterToGet.Text = my_config.parameter_to_get = ""

        try:
            self.parameterToSet.Text = str(my_config.parameter_to_set)
        except:
            self.parameterToSet.Text = my_config.parameter_to_set = ""

    def write_config(self):
        my_config.parameter_to_get = self.parameterToGet.Text
        my_config.parameter_to_set = self.parameterToSet.Text
        script.save_config()

    def _set_comboboxes(self):
        self.parameterToGet.ItemsSource = sorted(self.parameters_dict.keys())
        self.parameterToSet.ItemsSource = sorted(self.parameters_editable.keys())

    @property
    def parameter_to_get(self):
        p = self.parameters_editable[self.parameterToGet.Text]
        return p

    @property
    def parameter_to_set(self):
        p = self.parameters_editable[self.parameterToSet.Text]
        return p

    def run(self, sender, args):
        count_changed = 0

        # find not empty parameter
        definition_set = self.parameter_to_set.Definition
        definition_get = self.parameter_to_get.Definition
        not_empty_list = []
        skip_ids = []
        for e in self.selection:
            param = e.get_Parameter(definition_set)
            param_get = e.get_Parameter(definition_get)
            if param.AsString() != '' and param.AsString() != None and param.AsString() != param_get.AsString():
                not_empty_list.append("Target: %s, Source: %s" % (str(param.AsString()), str(param_get.AsString())))

                skip_ids.append(e.Id)

        if len(not_empty_list) > 0:
            len_limit = 10
            len_not_empty_list = len(not_empty_list)
            if len_not_empty_list > len_limit:
                not_empty_list = not_empty_list[:len_limit] + [' + %d more...' % (len_not_empty_list - len_limit)]

            text = "%d elements have values already. Replace them?:" % len_not_empty_list + "\n".join(not_empty_list)
            a = TaskDialog.Show(__title__, text,
                                TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No)
            if str(a) == "Yes":
                skip_ids = []

        t = Transaction(doc, __title__)
        t.Start()

        for e in self.selection:
            if e.Id in skip_ids:
                continue

            param = e.get_Parameter(definition_set)
            param_get = e.get_Parameter(definition_get)

            if param.AsString() == param_get.AsString():
                continue


            self.parameter_value_set(param, param_get.AsString())
            count_changed += 1

        self.write_config()

        if count_changed:
            t.Commit()
            TaskDialog.Show(__title__, "%d of %d elements updated" % (count_changed, len(self.selection),))
        else:
            t.RollBack()
            TaskDialog.Show(__title__, "Nothing was changed")

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

    def parameter_value_set(self, parameter, value):
        if parameter.StorageType == StorageType.Double or parameter.StorageType == StorageType.Integer:
            parameter.SetValueString(value)
        else:
            parameter.Set(str(value))

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

    def select_parameters(self):
        parameters_dict = self.get_selection_parameters(self.selection)
        parameters_editable = self.filter_editable(parameters_dict)

        options = []
        for param_id, param in parameters_editable.items():
            cb = CheckBoxParameter(param)
            options.append(cb)

        selected = SelectFromList.show(options, title='Parameter to replace', width=300,
                                       button_name='OK')

        return selected


def main():
    # Input
    sel = selection.elements
    CopyParameterWindow('window.xaml', sel).ShowDialog()


if __name__ == "__main__":
    main()
