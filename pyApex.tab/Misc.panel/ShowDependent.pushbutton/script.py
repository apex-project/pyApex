# -*- coding: utf-8 -*-
__title__ = 'Show\nDependent'
__doc__ = """List elements dependent on selected levels. To setup exceptions and limit run with Shift-click.
Context: You can either activate a Plan View, select Plan Views in project browser or select Levels on a section. If nothing selected, you'll be able to choise levels from a list.

Выдает список элементов, зависимых от выбранных видов. Для настроек исключения и ограничения кол-ва элементов, которые выводятся в списке, запустите с зажатым Shift
Контекст: Можно либо активировать План, либо выбрать Планы в Браузере проекта, либо выбрать уровни на разрезе или фасаде. Если ничего не выбрано, вам будет предложено выбрать уровнь из списка."""

__helpurl__ = "https://apex-project.github.io/pyApex/help#show-dependent"


try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr
    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >=4 and PYREVIT_VERSION.minor >=5

if pyRevitNewer44:
    from pyrevit import script, revit
    from pyrevit.revit import uidoc, doc
    from pyrevit.forms import SelectFromCheckBoxes, CommandSwitchWindow
    output = script.get_output()
    logger = script.get_logger()
    linkify = output.linkify
    selection = revit.get_selection()
    my_config = script.get_config()

else:
    from scriptutils import logger, this_script as script
    from revitutils import doc, selection, uidoc
    from scriptutils.userinput import SelectFromCheckBoxes, CommandSwitchWindow
    output = script.output
    my_config = script.config

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
import operator

def config_exceptions():
    try:
        v = my_config.exceptions
    except:
        import show_dependent_defaults as cdef
        v = cdef.exceptions

        my_config.exceptions = v
        script.save_config()

    return v


def config_limit():
    try:
        v = my_config.limit
    except:
        import show_dependent_defaults as cdef
        v = cdef.limit

        my_config.limit = v
        script.save_config()

    return v


class CheckBox:
    def __init__(self, element, name=None, default_state=False):
        self.element = element

        if name:
            self.name = name
        else:
            self.name = element.Name
        self.state = default_state

    def __str__(self):
        return self.name

    def __nonzero__(self):
        return self.state

    def __bool__(self):
        return self.state


def all_levels():
    cl = FilteredElementCollector(doc)
    all = cl.OfCategory(BuiltInCategory.OST_Levels).WhereElementIsNotElementType().ToElements()
    all_sorted = sorted(all, key=lambda l: l.Name)
    return all_sorted


def all_worksets():
    cl = FilteredWorksetCollector(doc)
    all = cl.OfKind(WorksetKind.UserWorkset)
    all_sorted = sorted(all, key=lambda l:l.Name)
    return all_sorted


def select_levels_dialog(elements_all, name = "parent object"):
    options = []

    for e in elements_all:
        cb = CheckBox(e, e.Name.replace("_","__"))
        options.append(cb)

    selected = SelectFromCheckBoxes.show(options, title='Select %s to check' % name, width=300,
                                         button_name='Select')
    if not selected:
        return

    return [c.element for c in selected if c.state is True]


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


def group_by_type(elements_ids):
    ignore_types = config_exceptions()

    result_dict = {}

    for e_id in elements_ids:
        e = doc.GetElement(e_id)
        if not e:
            continue

        try:
            el_type = e.Category.Name
        except:
            el_type = "Other"

        

        if el_type in ignore_types:
            continue

        el_type_full = el_type + " - " + e.GetType().Name.ToString()
        if el_type_full not in result_dict:
            result_dict[el_type_full] = []
        result_dict[el_type_full].append(e_id)

    return result_dict


def level_dependent():
    """By level"""
    levels_all = all_levels()
    if len(levels_all) < 2:
        print("At least 2 levels should be created in a project to check dependent. Create one more level and run again")
        return

    selected_levels = get_levels_from_selection(selection.elements)

    if len(selected_levels) == 0:
        selected_levels = select_levels_dialog(levels_all)
        if not selected_levels:
            print("Nothing selected")
            return

    results = {}
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

        results[e.Name] = group_by_type(elements)

    return results


def workset_dependent():
    """By workset"""

    selected_worksets = select_levels_dialog(all_worksets())
    if not selected_worksets:
        print("Nothing selected")
        return

    results = {}

    for ws in selected_worksets:
        elementCollector = FilteredElementCollector(doc)
        elementWorksetFilter = ElementWorksetFilter(ws.Id, False)
        element_ids = elementCollector.WherePasses(elementWorksetFilter).ToElementIds()

        results[ws.Name] = group_by_type(element_ids)

    return results


def print_elements_for_parent(result_dict, parent_name):
    """
    Print dictionary as list of clickable elements ids grouped by type, etc


    :param result_dict: {parent: {type: [element_ids]} }
    :param parent_name:
    """

    limit = config_limit()

    print(parent_name)

    e_ids = set()
    limited_count = 0

    # show types : count only
    if limit == 0:
        counts =  dict(map(lambda (k, v): (k, len(v)), result_dict.iteritems()))
        counts_sorted = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)
        for key, count in counts_sorted:
            print('{}: {}'.format(key, count))

    # show types : elements ids
    else:
        ids_limited = []
        for key, ids in result_dict.items():
            if pyRevitNewer44:
                print('{} - {}:'.format( key, output.linkify(ids, title=len(ids) ) ) )
            else:
                print('{} - {}:'.format( key, len(ids) ))

            e_ids |= set(ids)
            ids_limited = ids[:limit]

            limited_suffix = ""
            if len(ids_limited) != len(ids):
                limited_delta = len(ids) - len(ids_limited)
                limited_suffix = " +%d..." % (limited_delta)

                limited_count += limited_delta

            print(','.join(
                map(lambda x: output.linkify(x), ids_limited)
            ) + limited_suffix)

            print('\n\n')

        if pyRevitNewer44:
            print('{}'.format(output.linkify(list(e_ids),
                                             title='%d elements on %s' % (len(e_ids), parent_name))))
        else:
            print('%d elements on %s' % (len(e_ids), parent_name))

    print("\n\n\n")


def print_elements(data):
    for parent_name, result_dict in data.items():
        print_elements_for_parent(result_dict, parent_name)


def method_switch():
    available_methods = [
        level_dependent
    ]
    if doc.IsWorkshared:
        available_methods.append(workset_dependent)

    available_methods_dict = dict(
        (f.__doc__.split("\n")[0], f)
        for f in available_methods
    )
    if pyRevitNewer44:
        selected_switch = CommandSwitchWindow.show(available_methods_dict.keys(),
                                                   message='Select method')
    else:
        selected_switch = CommandSwitchWindow(available_methods_dict.keys(),
                                                   message='Select method').pick_cmd_switch()
    return available_methods_dict.get(selected_switch)


def main():
    func = method_switch()
    if not func:
        return
    data = func()
    if not data:
        return
    print_elements(data)


if __name__ == '__main__':
    main()
