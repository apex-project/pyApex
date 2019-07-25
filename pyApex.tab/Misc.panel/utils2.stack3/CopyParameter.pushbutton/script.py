# -*- coding: utf-8 -*-
__title__ = 'Copy parameter'
__doc__ = """Set value of one parameter to another one. Works with selected element or elements.

Shift-Click: change parameters by name

Записывает значение одного параметра в другой параметр выбранного элемента(ов)."""

__helpurl__ = "https://apex-project.github.io/pyApex/help#copy-paramter"
__context__ = 'Selection'
USE_NAMES = __shiftclick__

try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr

    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

try:
    pyRevitNewer4619 = PYREVIT_VERSION.major >= 4 and PYREVIT_VERSION.minor >= 6 and int(
        PYREVIT_VERSION.metadata[1:]) >= 24
except:
    pyRevitNewer4619 = False

from pyrevit import script, revit
from pyrevit.forms import WPFWindow, SelectFromList
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, TaskDialogResult
from Autodesk.Revit.DB import StorageType, Transaction
import pyapex_parameters as pyap
import pyapex_utils

selection = revit.selection.get_selection()
my_config = script.get_config()
logger = script.get_logger()

doc = revit.doc


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
            if my_config.parameter_to_get not in self.parameters_dict.keys():
                my_config.parameter_to_get = ""
        except:
            pass
        try:
            if my_config.parameter_to_set not in self.parameters_editable.keys():
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
        my_config.parameter_to_get = self.parameterToGet.Text.encode('utf-8')
        my_config.parameter_to_set = self.parameterToSet.Text.encode('utf-8')
        script.save_config()

    def _set_comboboxes(self):
        self.parameterToGet.ItemsSource = sorted(self.parameters_dict.keys())
        self.parameterToSet.ItemsSource = sorted(self.parameters_editable.keys())

    @property
    def parameter_to_get(self):
        p = self.parameters_dict[self.parameterToGet.Text]
        return p

    @property
    def parameter_to_set(self):
        p = self.parameters_editable[self.parameterToSet.Text]
        return p

    def run(self, sender, args):
        try:

            count_changed = 0
            # find not empty parameter
            definition_set = self.parameter_to_set.Definition
            definition_get = self.parameter_to_get.Definition

            # collect ones to be updated - parameters_get which aren't empty and aren't equal
            not_empty_list = []
            skip_ids = []
            errors_list_ids = []
            errors_list = []
            errors_text = ""
            for e in self.selection:
                if USE_NAMES:
                    param = e.LookupParameter(definition_set.Name)
                    param_get = e.LookupParameter(definition_get.Name)
                else:
                    param = e.get_Parameter(definition_set)
                    param_get = e.get_Parameter(definition_get)

                if not param or not param_get:
                    logger.debug("One of parameters not found for e.Id:%d" % e.Id.IntegerValue)
                    continue
                if not pyap.is_empty(param) and not pyap.are_equal(param, param_get):
                    value_get, value_set = pyap.convert_value(param_get, param, return_both=True)
                    not_empty_list.append("Target: %s, Source: %s" % (value_set, value_get))
                    skip_ids.append(e.Id)

            if len(not_empty_list) > 0:
                len_limit = 10
                len_not_empty_list = len(not_empty_list)
                if len_not_empty_list > len_limit:
                    not_empty_list = not_empty_list[:len_limit] + [' + %d more...' % (len_not_empty_list - len_limit)]

                text = "%d elements have values already. Replace them?\n" % len_not_empty_list + "\n".join(
                    not_empty_list)
                a = TaskDialog.Show(__title__, text,
                                    TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No)
                if a == TaskDialogResult.Yes:
                    skip_ids = []

            t = Transaction(doc, __title__)
            t.Start()
            for e in self.selection:
                if USE_NAMES:
                    param = e.LookupParameter(definition_set.Name)
                    param_get = e.LookupParameter(definition_get.Name)
                    if not param or not param_get:
                        logger.debug("One of parameters not found for e.Id:%d" % e.Id.IntegerValue)
                        continue
                else:
                    param = e.get_Parameter(definition_set)
                    param_get = e.get_Parameter(definition_get)
                _definition_set = param.Definition
                _definition_get = param_get.Definition

                if e.Id in skip_ids:
                    continue
                try:
                    if pyap.copy_parameter(e, _definition_get, _definition_set):
                        count_changed += 1
                except Exception as exc:
                    errors_list_ids.append(e.Id)
                    errors_list.append("Id: %d, exception: %s" % (e.Id.IntegerValue, str(exc)))
            if errors_list:
                errors_text = ("\n\nErrors occurred with %d elements :\n" % len(errors_list)) + \
                              "\n".join(errors_list[:5])
                if len(errors_list) > 5:
                    errors_text += "\n..."
                errors_text += "\n\nValues weren't changed, elements with errors selected"
                selection.set_to(errors_list_ids)

            if count_changed or errors_list:
                t.Commit()
                TaskDialog.Show(__title__,
                                "%d of %d elements updated%s" % (count_changed, len(self.selection), errors_text))
            else:
                t.RollBack()
                TaskDialog.Show(__title__, "Nothing was changed")
            logger.debug("finished")
        except Exception as exc:
            logger.error(exc)

        # TODO FIX do not write config in lower versions - risk to corrupt config
        if pyRevitNewer4619 or (
                pyapex_utils.is_ascii(self.parameterToGet.Text) and
                pyapex_utils.is_ascii(self.parameterToSet.Text)):
            try:
                self.write_config()
            except:
                logger.warn("Cannot save config")
        self.Close()

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
                v = pyap.parameter_value_get(param)
            if v:
                result[e] = v

        return result


    def parameter_key(self, parameter):
        if USE_NAMES:
            p_key = parameter.Definition.Name
        else:
            p_key = parameter.Definition.Id
        return p_key


    def get_selection_parameters(self, elements):
        """
        Get parameters which are common for all selected elements

        :param elements: Elements list
        :return: dict - {parameter_name: Parameter}
        """
        result = {}
        all_parameter_set = set()
        all_parameter_dict = dict()
        all_parameter_ids_by_element = {}

        # find all ids
        for e in elements:
            for p in e.Parameters:
                p_key = self.parameter_key(p)
                if p_key not in all_parameter_dict.keys():
                    all_parameter_dict[p_key] = p

                if e.Id not in all_parameter_ids_by_element.keys():
                    all_parameter_ids_by_element[e.Id] = set()
                all_parameter_ids_by_element[e.Id].add(p_key)

        # filter
        if USE_NAMES: # do not filter for names
            for p_key, p in all_parameter_dict.items():
                result[p.Definition.Name] = p
        else:
            for p_key, p in all_parameter_dict.items():
                exists_for_all_elements = True
                for e_id, e_params in all_parameter_ids_by_element.items():
                    if p_key not in e_params:
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
