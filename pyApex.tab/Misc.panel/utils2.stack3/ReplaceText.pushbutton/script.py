# -*- coding: utf-8 -*-
__title__ = 'Replace text'
__doc__ = """Find and replace text parameter for selected elements.

Находит и заменяет текстовые параметры для выделенных элементов"""

__context__ = 'Selection'

__helpurl__ = "https://apex-project.github.io/pyApex/help#replace-text"

from Autodesk.Revit.UI import TaskDialog
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


class ReplaceTextWindow(WPFWindow):
    def __init__(self, xaml_file_name, selected_elements):
        self.selection = selected_elements
        if not self.selection:
            TaskDialog.Show(__title__, "election error or wrong elements were selected")
            return

        parameter_to_set = self.select_parameters()

        if not parameter_to_set:
            TaskDialog.Show(__title__, "Nothing selected")
            return

        self.parameter_to_set = parameter_to_set[0].parameter

        WPFWindow.__init__(self, xaml_file_name)

    @property
    def text_find(self):
        return self.textFind.Text

    @property
    def text_replace(self):
        return self.textReplace.Text

    def run(self, sender, args):
        text_find = self.text_find
        text_replace = self.text_replace
        count_changed = 0
        t = Transaction(doc, __title__)
        t.Start()

        for e in self.selection:
            definition = self.parameter_to_set.Definition
            param = e.get_Parameter(definition)
            param_before = param.AsString()
            param_after = param_before.replace(text_find, text_replace)

            if param_before != param_after:
                count_changed += 1
                self.parameter_value_set(param, param_after)

        if count_changed:
            t.Commit()
            TaskDialog.Show(__title__, "%d of %d elements updated" % (count_changed, len(self.selection),))
        else:
            t.RollBack()
            TaskDialog.Show(__title__, "Nothing was updated")

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

    def parameter_value_set(self, parameter, value, text_format=None):
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
                result[p.Id] = p

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
    ReplaceTextWindow('window.xaml', sel).ShowDialog()


if __name__ == "__main__":
    main()
