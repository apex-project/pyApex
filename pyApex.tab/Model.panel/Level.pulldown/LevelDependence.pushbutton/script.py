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
    from pyrevit.forms import SelectFromList, SelectFromCheckBoxes
    output = script.get_output()
    logger = script.get_logger()
    linkify = output.linkify
    selection = revit.get_selection()
    uidoc = revit.uidoc
    doc = revit.doc
else:
    from scriptutils import logger
    from scriptutils.userinput import SelectFromList, SelectFromCheckBoxes
    from revitutils import doc, selection, uidoc

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
ignore_types = [Level, SunAndShadowSettings, Viewport, SketchPlane, Sketch]


#filter
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


selected_levels = get_levels_from_selection(selection.elements)

limit = 50

if len(selected_levels) == 0:
    logger.error('Please, select level or plan view')
else:
    opened_view_ids = uidoc.GetOpenUIViews()

    result_dict = {}
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
            if type(e_del) in ignore_types:
                ignored += 1
                continue

            element_ids.append(e_del_id)

            if i <= limit or limit == 0:
                i += 1
                try:
                    el_type = e_del.Category.Name
                except:
                    el_type = "Other"
                if el_type not in result_dict:
                    result_dict[el_type] = []
                result_dict[el_type].append(e_del_id)


        elements_count = len(element_ids)

        for key, ids in result_dict.items():
            print('{} - {}:'.format( key, output.linkify(ids, title=len(ids) ) ) )
            print(','.join(
                map(lambda x: output.linkify(x), ids)
            ))
            print('\n\n')

        if i == limit:
            print("+ %d more elements ..." % (elements_count - limit))

        if ignored > 0:
            print("%d elements ignored" % ignored)

        print('{}'.format(output.linkify(element_ids,
                                         title='%d elements on level %s' % (elements_count, e.Name))))
        element_ids_str = map(lambda x: str(x.IntegerValue), element_ids)
        print("\n\t"  + ",".join(element_ids_str))
        print("\n\n\n")

