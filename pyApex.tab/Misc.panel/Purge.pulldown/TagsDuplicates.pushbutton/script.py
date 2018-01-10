# -*- coding: utf-8 -*-
__title__ = 'Find duplicate\nTags'
__doc__ = """Select duplicates tags on active view\nShitf+Click - on all views"""

__helpurl__ = "https://apex-project.github.io/pyApex/help#find-duplicate-tags"

try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr
    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >=4 and PYREVIT_VERSION.minor >=5


if pyRevitNewer44:
    from pyrevit import script, revit
    from pyrevit.revit import uidoc, doc
    from pyrevit.forms import CommandSwitchWindow
    output = script.get_output()
    logger = script.get_logger()
    linkify = output.linkify
    selection = revit.get_selection()
    my_config = script.get_config()

else:
    from scriptutils import logger, this_script as script
    from revitutils import doc, selection, uidoc
    from scriptutils.userinput import CommandSwitchWindow
    output = script.output
    my_config = script.config

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ViewType
from Autodesk.Revit.DB import BuiltInCategory, ElementId
from System.Collections.Generic import List

# TODO think how to implement parent-parameter selection (tag.Door, tag.Room etc.)
switches = {
    "RoomTags": BuiltInCategory.OST_RoomTags,
    "AreaTags": BuiltInCategory.OST_AreaTags,
    "DoorTags": BuiltInCategory.OST_DoorTags,
    "WindowTags": BuiltInCategory.OST_WindowTags,
    # "WallTags": BuiltInCategory.OST_WallTags,
}


def select_tags_by_view(selected_switch):
    tags_by_view = {}

    cat = switches[selected_switch]

    cl_tags = FilteredElementCollector(doc)
    tags = cl_tags.OfCategory(cat)

    # Find only current view tags, if not ShiftClick
    if not __shiftclick__:
        tags = tags.OwnedByView(doc.ActiveView.Id)

    tags = tags.WhereElementIsNotElementType().ToElements()

    logger.debug(str(len(tags)) + " tags found")

    for e in tags:
        v = e.OwnerViewId
        if v not in tags_by_view.keys():
            tags_by_view[v] = []
        tags_by_view[v].append(e)

    return tags_by_view


def find_duplicates_on_view(tags):
    tags_dict = {}
    for tag in tags:
        try:
            # TODO find the way to check tags connected to linked file
            k = tag.Room.Id
        except:
            continue

        if k not in tags_dict:
            tags_dict[k] = []

        tags_dict[k].append(tag.Id)
        # except:
        #     logger.info(str(tag.Id) + " unknown exception")

    duplicates_id = []

    for t in tags_dict.keys():
        if len(tags_dict[t]) > 1:
            tags_sorted = sorted(tags_dict[t], key = lambda x: x.IntegerValue)
            # append all ids except the first
            duplicates_id += list(tags_sorted)[1:]

    return duplicates_id


def select_duplicate_tags(selected_switch):
    tags_by_view = select_tags_by_view(selected_switch)

    duplicates_id = []
    for view, tags in tags_by_view.items():
        duplicates_id_view = find_duplicates_on_view(tags)
        duplicates_id += duplicates_id_view
        dup_count = len(duplicates_id_view)
        if len(tags_by_view.keys()) > 1 and dup_count > 0:
            view_name = doc.GetElement(view).Name
            print("View \"%s\": %d of %d tags duplicated" % (
                view_name, dup_count, len(tags) )
                  )

    if pyRevitNewer44:
        selection.set_to(duplicates_id)
    else:
        collection = List[ElementId](duplicates_id)
        selection.SetElementIds(collection)

    print("%d duplicated %s selected" % (len(duplicates_id), selected_switch))


def main():
    selected_switch = CommandSwitchWindow.show(switches.keys(),
                                               message='Select tag type')
    if selected_switch:
        select_duplicate_tags(selected_switch)


if __name__ == '__main__':
    main()
