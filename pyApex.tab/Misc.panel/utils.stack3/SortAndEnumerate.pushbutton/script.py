# -*- coding: utf-8 -*-
__title__ = 'Sort and enumerate'
__doc__ = """Sort selected objects, views or sheets by specified parameter, coordinate or along curve. 
Then write order number of each element as another parameter

Context: at least 2 objects must be selected

Сортирует выделенные объекты, виды или листы по определенному параметру, координате или вдоль линии.
Затем записывает порядковый номер каждого из объектов в другой параметр.

Контекст: как минимум 2 объекта должны быть выделены"""

__context__ = 'Selection'

__helpurl__ = "https://apex-project.github.io/pyApex/help#sort-and-enumerate"

import operator

from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, Selection
from Autodesk.Revit.DB import BuiltInCategory, ElementId, Definition, StorageType

from Autodesk.Revit.DB import Transaction, TransactionGroup

from pyrevit import script, forms
from pyrevit.forms import WPFWindow

logger = script.get_logger()
from pyrevit.revit import doc, selection as _selection_pyr
from curve_chain import pick_chain, chain_closest_point
selection_pyr = _selection_pyr.get_selection()
selection_elements = selection_pyr.elements
my_config = script.get_config()
wpf_window = None

# def get_selection():
#     """
#     Get selected objects / sheets / views or allows user to select
#
#     :return: selected objects or None
#     """
#     return selection_doc.elements

def sort_joined_curves(curves):
    adjoinedcurves = curves
    count = 0
    end = 0
    while len(adjoinedcurves) > 0 and count < 100:
        c = curves[0]
        result = []
        adjoinedcurves = c.GetAdjoinedCurveElements(0)
        count += 1

class EnumerateWindow(WPFWindow):
    def __init__(self, xaml_file_name, selected_elements):
        is_geom_list, not_geom_list = self.separate_geometry(selected_elements)
        self.selection, self.is_geom = self.filter_geometry_and_other(is_geom_list, not_geom_list)

        self.extra_geom_keys = [
                                "<Along curve>",
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
        # check are last parameters available
        try:
            if my_config.parameter_to_sort not in self.parameters_sortable:
                my_config.parameter_to_sort = ""
        except:
            pass
        try:
            if my_config.parameter_to_set not in self.parameters_editable:
                my_config.parameter_to_set = ""
        except:
            pass

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
        my_config.parameter_to_set = self.parameterToSet.Text
        my_config.is_reversed = self.isReversed.IsChecked
        script.save_config()
    #
    # def parameterToSort_changed(self, sender, args):
    #     if sender.SelectedItem == "<Along curve>":
    #         forms.alert("Select curve to sort along")
    #         self.Hide()
    #         try:
    #             chain, chain_is_reversed = pick_chain(True)
    #         except Exception as exc:
    #             logger.error(exc)
    #         self.Show()
    #         logger.info(chain)
    #         logger.info(chain_is_reversed)
    #     elif sender.SelectedItem == "---" and self.parameterToSort.Text != "---":
    #         self.parameterToSort.Text = self.parameterToSort.Text

    @property
    def parameter_to_sort(self):
        p = self.parameterToSort.Text
        if not self.parameterToSort or self.parameterToSort.Text == "":
            return
        if type(p) == str and p in self.extra_geom_keys:
            return p
        else:
            return self.parameters_sortable[p]

    @property
    def parameter_to_set(self):
        if not self.parameterToSet or self.parameterToSet.Text == "":
            return
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
        # print(dir(self))
        if not(self.parameter_to_sort and  self.parameter_to_sort != "" and self.parameter_to_set and  self.parameter_to_set != ""):
            forms.alert("Error! All the parameters should be set")
            return

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

        # selection_doc.set self.selection
        try:
            self.write_config()
        except:
            pass
        logger.debug("run - set_to", map(lambda e: e[0].Id.IntegerValue, result))
        selection_pyr.set_to(map(lambda e: e[0].Id, result))
        self.Close()


    def sort(self, elements, parameter_to_sort, reverse=False):
        param_dict = self.element_parameter_dict(elements, parameter_to_sort)
        param_dict_sorted = sorted(param_dict.items(), key=operator.itemgetter(1), reverse=reverse)
        return param_dict_sorted
        # return map(lambda x: x[0], param_dict_sorted)


    def element_parameter_dict(self, elements, parameter_to_sort):
        result = {}
        chain, chain_is_reversed = (None, None)
        if parameter_to_sort == "<Along curve>":
            forms.alert("Select curve to sort along")
            self.Hide()
            try:
                chain, chain_is_reversed = pick_chain(doc)
            except Exception as exc:
                logger.error(exc)
            self.Show()
            logger.debug(chain)
            logger.debug(chain_is_reversed)

        for e in elements:
            if type(parameter_to_sort) == str:
                if parameter_to_sort[0] == "<" and parameter_to_sort[2:] == " coordinate>":
                    parameter_loc = parameter_to_sort[1]
                    loc_point = e.Location.Point
                    v = getattr(loc_point, parameter_loc)
                elif parameter_to_sort == "<Along curve>" and chain:
                    logger.debug("<Along curve>")
                    loc_point = e.Location.Point
                    v = chain_closest_point(loc_point, chain, chain_is_reversed, doc)
                else:
                    logger.error("Parameter error")
                    return
            else:
                param = e.get_Parameter(parameter_to_sort.Definition)
                v = self.parameter_value_get(param)
            if v:
                logger.debug("v: %s" % v)
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
                if param:
                    # TODO figure out why param is None here
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
    global wpf_window
    # Input
    if not selection_elements:
        logger.error("Nothing selected")
        return

    if len(selection_elements) < 2:
        logger.error('At least 2 elements or views must be selected.')
        return

    logger.debug("main - selection", map(lambda e: e.Id.IntegerValue, selection_elements))
    wpf_window = EnumerateWindow('window.xaml', selection_elements)
    # print(dir(wpf_window))
    wpf_window.show(True)
    # print(dir(wpf_window))



if __name__ == "__main__":
    main()
