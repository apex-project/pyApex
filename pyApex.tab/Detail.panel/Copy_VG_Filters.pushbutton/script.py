# -*- coding: utf-8 -*-
__title__ = 'Copy VG filters'
__doc__ = """Copying filter overrides from selected or active view to chosen view templates. 
If VG override for this filter already exists in a template it will be updated.

Context: Select or activate a view

Копирует настройки фильтров из настроек "Переопределения видимости/графики" для текущего вида в выбраныне шеблоны видов.
Если для фильтра уже заданы переопределения в целевом шаблоне, они будут обновлены.

Контекст: Выбранный или активный вид
"""

__helpurl__ = "https://apex-project.github.io/pyApex/help#copy-vg-filters"

import clr
import os
import os.path as op
import pickle as pl

from System.Collections.Generic import List
from Autodesk.Revit.DB import *

try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr

    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >= 4 and PYREVIT_VERSION.minor >= 5

if pyRevitNewer44:
    from pyrevit import script, revit
    from pyrevit.forms import SelectFromList

    output = script.get_output()
    logger = script.get_logger()
    linkify = output.linkify
    from pyrevit.revit import doc, uidoc, selection

    selection = selection.get_selection()

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


usertemp = os.getenv('Temp')
prjname = op.splitext(op.basename(doc.PathName))[0]

datafile = usertemp + '\\' + prjname + '_pyChecked_Templates.pym'
logger.info(datafile)

sel_set = []

allowed_types = [
    ViewPlan,
    View3D,
    ViewSection,
    ViewSheet,
    ViewDrafting
]


def read_checkboxes_state():
    try:
        f = open(datafile, 'r')
        cursel = pl.load(f)
        f.close()

        sel_set = []
        for elId in cursel:
            sel_set.append(int(elId))

        return sel_set
    except:
        return []


def save_checkboxes_state(checkboxes):
    selected_ids = {c.Id.IntegerValue.ToString() for c in checkboxes}
    f = open(datafile, 'w')
    pl.dump(selected_ids, f)
    f.close()


def get_filter_rules(doc):
    cl = FilteredElementCollector(doc).WhereElementIsNotElementType()
    els = cl.OfClass(type(ElementInstance)).ToElementIds()
    return els


def get_view_templates(doc, view_type=None, sel_set=sel_set):
    cl_view_templates = FilteredElementCollector(doc).WhereElementIsNotElementType()
    allview_templates = cl_view_templates.OfCategory(BuiltInCategory.OST_Views).ToElementIds()

    vt_list = []
    for vtId in allview_templates:
        vt = doc.GetElement(vtId)
        if vt.IsTemplate:
            if view_type is None or vt.ViewType == view_type:
                vt_list.append(vt)
    return vt_list


def get_view_filters(doc, v):
    result = []
    ftrs = v.GetFilters()
    for fId in ftrs:
        f = doc.GetElement(fId)
        result.append(f)
    return result


def get_active_view():
    if type(doc.ActiveView) != View:
        active_view = doc.ActiveView
    else:
        if len(selected_ids) == 0:
            logger.error('Select a view with applied template, to copy filters from it')
            return

        active_view = doc.GetElement(selected_ids[0])

        if type(active_view) not in allowed_types:
            logger.error('Selected view is not allowed. Please select or open view from which '
                         'you want to copy template settings VG Overrides - Filters')
            return
    return active_view


def main():
    active_view = get_active_view()
    if not active_view:
        logger.warning('Activate a view to copy')
        return

    logger.info('Source view selected: %s id%s' % (active_view.Name, active_view.Id.ToString()))

    """
    Filters selection
    """
    active_template_filters_ch = get_view_filters(doc, active_view)

    sel_set = read_checkboxes_state()
    vt_list = get_view_templates(doc, sel_set=sel_set)

    if not vt_list:
        logger.warning('Project has no view templates')
        return

    if not active_template_filters_ch:
        logger.warning('Active view has no filter overrides')
        return

    filter_checkboxes = SelectFromList.show(active_template_filters_ch, name_attr='Name',
                                            title='Select filters to copy',
                                            button_name='Select filters', multiselect=True)
    filter_checkboxes_sel = []

    # Select filters from active view
    for checkbox in filter_checkboxes:
        if checkbox:
            filter_checkboxes_sel.append(checkbox)

    if not filter_checkboxes_sel:
        return

    """
    Target view templates selection
    """
    view_checkboxes = SelectFromList.show(vt_list, name_attr='Name', title='Select templates to apply filters',
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

        for f in filter_checkboxes_sel:
            try:
                vt.RemoveFilter(f.Id)
                logger.info('filter %s deleted from template %s' % (f.Id.IntegerValue.ToString(), vt.Name))
            except:
                pass

            try:
                fr = active_view.GetFilterOverrides(f.Id)
                vt.SetFilterOverrides(f.Id, fr)
            except Exception as e:
                logger.warning('filter %s was not aplied to view %s\n%s' % (f.Id.IntegerValue.ToString(),
                                                                            vt.Name, e))

    t.Commit()

    print("Completed")


if __name__ == "__main__":
    main()
