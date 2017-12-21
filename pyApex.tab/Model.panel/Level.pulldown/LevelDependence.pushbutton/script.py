# -*- coding: utf-8 -*-
__title__ = 'Level dependencies'
__doc__ = 'List elements dependent of selected level\nYou can select plan view to check its level'

__helpurl__ = "https://apex-project.github.io/pyApex/help#level-dependencies"

try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr
    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >=4 and PYREVIT_VERSION.minor >=5

if pyRevitNewer44:
    from pyrevit import script, revit
    from pyrevit.revit import uidoc, doc
    from pyrevit.forms import SelectFromCheckBoxes
    output = script.get_output()
    logger = script.get_logger()
    linkify = output.linkify
    selection = revit.get_selection()
    my_config = script.get_config()
else:
    from scriptutils import logger, this_script as script
    from revitutils import doc, selection, uidoc
    from scriptutils.userinput import SelectFromCheckBoxes
    output = script.output
    my_config = script.config

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons


def get_config_exceptions():
    try:
        conf = my_config.exceptions

    except:
        import os
        config_default_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                           "ignore_types_default.txt")
        try:
            with open(config_default_path) as f:
                conf = f.readline()
        except:
            exceptions = []

        my_config.exceptions = conf
        script.save_config()

    if conf:
        exceptions = conf.split(",")
        exceptions = map(lambda x: x.strip(), exceptions)
        return exceptions


def get_config_limit():
    try:
        conf = int(my_config.limit)
    except:
        conf = 50
        script.config.limit = conf
        script.save_config()

    return conf


class CheckBoxLevel:
    def __init__(self, level, default_state=False):
        self.level = level
        self.name = level.Name
        self.state = default_state

    def __str__(self):
        return self.name

    def __nonzero__(self):
        return self.state

    def __bool__(self):
        return self.state


def all_levels():
    cl = FilteredElementCollector(doc)
    levels_all = cl.OfCategory(BuiltInCategory.OST_Levels).WhereElementIsNotElementType().ToElements()
    return levels_all


def select_levels_dialog(levels_all):
    options = []

    for l in levels_all:
        cb = CheckBoxLevel(l)
        options.append(cb)

    selected = SelectFromCheckBoxes.show(options, title='Select level to check', width=300,
                                         button_name='Select')
    if not selected:
        return

    return [c.level for c in selected if c.state is True]


# filter
def get_levels_from_selection(selected_elements):
    result = []
    for e in selection.elements:
        if type(e) == ViewPlan:
            e = e.GenLevel
        elif type(e) == Level:
            pass
        else:
            continue
        result.append(e)

    if len(result) == 0:
        if type(uidoc.ActiveView) == ViewPlan:
            l_id = uidoc.ActiveView.GenLevel
            result = [l_id]
    return result


def check_dependent_views(l):
    to_close = []

    for uiview in uidoc.GetOpenUIViews():
        v = doc.GetElement(uiview.ViewId)
        if not v.GenLevel:
            continue

        if v.GenLevel.Id == l.Id:
            to_close.append(uiview)

    return to_close


def starting_view():
    startingViewSettingsCollector = FilteredElementCollector(doc)
    startingViewSettingsCollector.OfClass(StartingViewSettings).ToElements()
    startingView = None


    for settings in startingViewSettingsCollector:
        startingView = doc.GetElement(settings.ViewId)

    return startingView


def main():
    ignore_types = get_config_exceptions()
    limit = get_config_limit()

    levels_all = all_levels()
    if len(levels_all) < 2:
        print("At least 2 levels should be created in a project to check dependencies. Create one more level and run again")
        return

    selected_levels = get_levels_from_selection(selection.elements)

    if len(selected_levels) == 0:
        selected_levels = select_levels_dialog(levels_all)
        if not selected_levels:
            print("Nothing selected")
            return

    for e in selected_levels:
        views_to_close = check_dependent_views(e)
        if len(views_to_close) > 0:

            q = TaskDialog.Show(__title__,
                                "These views will be closed:\n%s" % ", ".join(
                                    map(lambda x: doc.GetElement(x.ViewId).Name, views_to_close) ),
                                TaskDialogCommonButtons.Ok | TaskDialogCommonButtons.Cancel)

            if str(q) == "Cancel":
                break

            if len(uidoc.GetOpenUIViews()) == len(views_to_close):
                uidoc.ActiveView = starting_view()

            for v in views_to_close:
                v.Close()

        t = Transaction(doc, "Check level " + e.Name)
        t.Start()
        elements = doc.Delete(e.Id)
        t.RollBack()

        element_ids = []

        i = 0

        ignored = 0

        result_dict = {}

        print(e.Name)

        for e_del_id in elements:
            e_del = doc.GetElement(e_del_id)
            if not e_del:
                ignored += 1
                continue

            try:
                el_type = e_del.Category.Name
            except:
                el_type = "Other"

            if el_type in ignore_types:
                ignored += 1
                continue

            element_ids.append(e_del_id)

            if i <= limit or limit == 0:
                i += 1

                if el_type not in result_dict:
                    result_dict[el_type] = []
                result_dict[el_type].append(e_del_id)


        elements_count = len(element_ids)

        for key, ids in result_dict.items():
            if pyRevitNewer44:
                print('{} - {}:'.format( key, output.linkify(ids, title=len(ids) ) ) )
            else:
                print('{} - {}:'.format(key, len(ids) ))

            print(','.join(
                map(lambda x: output.linkify(x), ids)
            ))
            print('\n\n')

        if i == limit and elements_count - limit > 0:
            print("+ %d more elements ..." % (elements_count - limit))

        if ignored > 0:
            print("%d elements ignored" % ignored)

        if pyRevitNewer44:
            print('{}'.format(output.linkify(element_ids,
                                         title='%d elements on level %s' % (elements_count, e.Name))))
        else:
            print('%d elements on level %s' % (elements_count, e.Name))

        element_ids_str = map(lambda x: str(x.IntegerValue), element_ids)
        print("\n\t"  + ",".join(element_ids_str))
        print("\n\n\n")


if __name__ == '__main__':
    main()
