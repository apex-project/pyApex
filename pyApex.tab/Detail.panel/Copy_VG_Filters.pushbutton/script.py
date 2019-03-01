# -*- coding: utf-8 -*-
# pylint: skip-file
import clr
import os
import os.path as op
import pickle as pl

from System.Collections.Generic import List
from Autodesk.Revit.DB import *

from pyrevit import versionmgr


__title__ = 'Copy VG filters'
__helpurl__ = "https://apex-project.github.io/pyApex/help#copy-vg-filters"
__doc__ = """Copying filter overrides from selected or active view to chosen view templates. 
If VG override for this filter already exists in a template it will be updated.

Context: Select or activate a view

Копирует настройки фильтров из настроек "Переопределения видимости/графики" для текущего вида в выбраныне шеблоны видов.
Если для фильтра уже заданы переопределения в целевом шаблоне, они будут обновлены.

Контекст: Выбранный или активный вид
"""

PYREVIT_VERSION = versionmgr.get_pyrevit_version()

# if pyrevit is newer than 4.5 (major.minor)
if PYREVIT_VERSION.major >= 4 and PYREVIT_VERSION.minor >= 5:
    from pyrevit import script, revit
    from pyrevit.forms import SelectFromList
    from pyrevit.revit import doc, uidoc, selection
    output = script.get_output()
    logger = script.get_logger()
    linkify = output.linkify
    selection = selection.get_selection()
# otherwise use the older pyrevit api
else:
    from scriptutils import logger
    from scriptutils.userinput import SelectFromList
    from revitutils import doc, uidoc, selection

selected_ids = selection.element_ids


class CheckBoxOption:
    def __init__(self, name, id, sel_set=[], default_state=False):
        self.name = name
        self.id = id
        self.state = default_state
        if int(self.id.ToString()) in sel_set:
            self.state = True

    # define the __nonzero__ method so you can use your objects in an
    # if statement. e.g. if checkbox_option:
    def __nonzero__(self):
        return self.state

    # __bool__ is same as __nonzero__ but is for python 3 compatibility
    def __bool__(self):
        return self.state


USER_TEMP = os.getenv('Temp')
PROJECT_NAME = op.splitext(op.basename(doc.PathName))[0]

DATAFILE = USER_TEMP + '\\' + PROJECT_NAME + '_pyChecked_Templates.pym'
logger.debug(DATAFILE)

sel_set = []

ALLOWED_TYPES = [
    ViewPlan,
    View3D,
    ViewSection,
    ViewSheet,
    ViewDrafting
]


def read_checkboxes_state():
    try:
        with open(DATAFILE, 'r') as filter_element: 
            cursel = pl.load(filter_element)

        sel_set = []
        for elId in cursel:
            sel_set.append(int(elId))

        return sel_set
    except:
        return []


def save_checkboxes_state(checkboxes):
    selected_ids = {c.Id.IntegerValue.ToString() for c in checkboxes}
    with open(DATAFILE, 'w') as filter_element: 
        pl.dump(selected_ids, filter_element)


def get_filter_rules(doc):
    return FilteredElementCollector(doc).WhereElementIsNotElementType()\
                                        .OfClass(type(ElementInstance))\
                                        .ToElementIds()


def get_view_templates(doc, view_type=None, sel_set=sel_set):
    allview_templates = \
        FilteredElementCollector(doc).WhereElementIsNotElementType()\
                                     .OfCategory(BuiltInCategory.OST_Views)\
                                     .ToElementIds()

    viewtemplate_list = []
    for vtId in allview_templates:
        vt = doc.GetElement(vtId)
        if vt.IsTemplate:
            if view_type is None or vt.ViewType == view_type:
                viewtemplate_list.append(vt)
    return viewtemplate_list


def get_view_filters(doc, view):
    result = []
    for filter_id in view.GetFilters():
        filter_element = doc.GetElement(filter_id)
        result.append(filter_element)
    return result


def get_active_view():
    if isinstance(doc.ActiveView, View):
        active_view = doc.ActiveView
    else:
        if len(selected_ids) == 0:
            logger.error('Select a view with applied template, to copy filters from it')
            return

        active_view = doc.GetElement(selected_ids[0])

        if not isinstance(active_view, ALLOWED_TYPES):
            logger.error('Selected view is not allowed. Please select or open view from which '
                         'you want to copy template settings VG Overrides - Filters')
            return
    return active_view


def main():
    active_view = get_active_view()
    if not active_view:
        logger.warning('Activate a view to copy')
        return

    logger.debug('Source view selected: %s id%s' % (active_view.Name, active_view.Id.ToString()))

    # Filters selection =======================================================
    active_template_filters_ch = get_view_filters(doc, active_view)

    sel_set = read_checkboxes_state()
    viewtemplate_list = get_view_templates(doc, sel_set=sel_set)

    if not viewtemplate_list:
        logger.warning('Project has no view templates')
        return

    if not active_template_filters_ch:
        logger.warning('Active view has no filter overrides')
        return

    filter_checkboxes = \
        SelectFromList.show(
            active_template_filters_ch,
            name_attr='Name',
            title='Select filters to copy',
            button_name='Select filters',
            multiselect=True
        ) or []

    filter_checkboxes_sel = []

    # Select filters from active view
    for checkbox in filter_checkboxes:
        if checkbox:
            filter_checkboxes_sel.append(checkbox)

    if not filter_checkboxes_sel:
        return

    # Target view templates selection =========================================
    view_checkboxes = SelectFromList.show(viewtemplate_list, name_attr='Name', title='Select templates to apply filters',
                                          button_name='Apply filters to templates', multiselect=True)
    view_checkboxes_sel = []

    # Select view templates to copy
    for checkbox in view_checkboxes:
        if checkbox:
            view_checkboxes_sel.append(checkbox)

    if not view_checkboxes_sel:
        return

    save_checkboxes_state(view_checkboxes_sel)

    # active_template = doc.GetElement(active_view.ViewTemplateId)

    t = Transaction(doc)
    t.Start(__title__)

    for vt in view_checkboxes_sel:
        if vt.Id == active_view.ViewTemplateId:
            logger.debug('Current template found')
            continue

        for filter_element in filter_checkboxes_sel:
            try:
                vt.RemoveFilter(filter_element.Id)
                logger.debug('filter %s deleted from template %s' % (filter_element.Id.IntegerValue.ToString(), vt.Name))
            except:
                pass

            try:
                fr = active_view.GetFilterOverrides(filter_element.Id)
                vt.SetFilterOverrides(filter_element.Id, fr)
            except Exception as e:
                logger.warning('filter %s was not aplied to view %s\n%s' % (filter_element.Id.IntegerValue.ToString(),
                                                                            vt.Name, e))

    t.Commit()

    print("Completed")

if __name__ == "__main__":
    main()
