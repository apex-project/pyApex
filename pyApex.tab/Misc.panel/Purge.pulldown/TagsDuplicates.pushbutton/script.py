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

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ViewType, ElementId, AreaTag, FamilyInstance
from Autodesk.Revit.DB.Architecture import RoomTag

from System.Collections.Generic import List

# TODO think how to implement parent-parameter selection (tag.Door, tag.Room etc.)
switches = {
    "AreaLoadTags": BuiltInCategory.OST_AreaLoadTags,
    "AreaReinTags": BuiltInCategory.OST_AreaReinTags,
    "AreaTags": BuiltInCategory.OST_AreaTags,
    "BeamAnalyticalTags": BuiltInCategory.OST_BeamAnalyticalTags,
    "BeamSystemTags": BuiltInCategory.OST_BeamSystemTags,
    "BraceAnalyticalTags": BuiltInCategory.OST_BraceAnalyticalTags,
    "CableTrayFittingTags": BuiltInCategory.OST_CableTrayFittingTags,
    "CableTrayTags": BuiltInCategory.OST_CableTrayTags,
    "CaseworkTags": BuiltInCategory.OST_CaseworkTags,
    "CeilingTags": BuiltInCategory.OST_CeilingTags,
    "ColumnAnalyticalTags": BuiltInCategory.OST_ColumnAnalyticalTags,
    "CommunicationDeviceTags": BuiltInCategory.OST_CommunicationDeviceTags,
    "ConduitFittingTags": BuiltInCategory.OST_ConduitFittingTags,
    "ConduitTags": BuiltInCategory.OST_ConduitTags,
    "CouplerTags": BuiltInCategory.OST_CouplerTags,
    "CurtainWallPanelTags": BuiltInCategory.OST_CurtainWallPanelTags,
    "CurtaSystemTags": BuiltInCategory.OST_CurtaSystemTags,
    "DetailComponentTags": BuiltInCategory.OST_DetailComponentTags,
    "DoorTags": BuiltInCategory.OST_DoorTags,
    "DuctAccessoryTags": BuiltInCategory.OST_DuctAccessoryTags,
    "DuctFittingTags": BuiltInCategory.OST_DuctFittingTags,
    "DuctInsulationsTags": BuiltInCategory.OST_DuctInsulationsTags,
    "DuctLiningsTags": BuiltInCategory.OST_DuctLiningsTags,
    "DuctTags": BuiltInCategory.OST_DuctTags,
    "DuctTerminalTags": BuiltInCategory.OST_DuctTerminalTags,
    "ElectricalCircuitTags": BuiltInCategory.OST_ElectricalCircuitTags,
    "ElectricalEquipmentTags": BuiltInCategory.OST_ElectricalEquipmentTags,
    "ElectricalFixtureTags": BuiltInCategory.OST_ElectricalFixtureTags,
    "FabricAreaTags": BuiltInCategory.OST_FabricAreaTags,
    "FabricationContainmentTags": BuiltInCategory.OST_FabricationContainmentTags,
    "FabricationDuctworkTags": BuiltInCategory.OST_FabricationDuctworkTags,
    "FabricationHangerTags": BuiltInCategory.OST_FabricationHangerTags,
    "FabricationPipeworkTags": BuiltInCategory.OST_FabricationPipeworkTags,
    "FabricReinforcementTags": BuiltInCategory.OST_FabricReinforcementTags,
    "FireAlarmDeviceTags": BuiltInCategory.OST_FireAlarmDeviceTags,
    "FlexDuctTags": BuiltInCategory.OST_FlexDuctTags,
    "FlexPipeTags": BuiltInCategory.OST_FlexPipeTags,
    "FloorAnalyticalTags": BuiltInCategory.OST_FloorAnalyticalTags,
    "FloorTags": BuiltInCategory.OST_FloorTags,
    "FootingSpanDirectionSymbol": BuiltInCategory.OST_FootingSpanDirectionSymbol,
    "FoundationSlabAnalyticalTags": BuiltInCategory.OST_FoundationSlabAnalyticalTags,
    "FurnitureSystemTags": BuiltInCategory.OST_FurnitureSystemTags,
    "FurnitureTags": BuiltInCategory.OST_FurnitureTags,
    "GenericModelTags": BuiltInCategory.OST_GenericModelTags,
    "HostFinTags": BuiltInCategory.OST_HostFinTags,
    "InternalAreaLoadTags": BuiltInCategory.OST_InternalAreaLoadTags,
    "InternalLineLoadTags": BuiltInCategory.OST_InternalLineLoadTags,
    "InternalPointLoadTags": BuiltInCategory.OST_InternalPointLoadTags,
    "IsolatedFoundationAnalyticalTags": BuiltInCategory.OST_IsolatedFoundationAnalyticalTags,
    "KeynoteTags": BuiltInCategory.OST_KeynoteTags,
    "LightingDeviceTags": BuiltInCategory.OST_LightingDeviceTags,
    "LightingFixtureTags": BuiltInCategory.OST_LightingFixtureTags,
    "LineLoadTags": BuiltInCategory.OST_LineLoadTags,
    "LinkAnalyticalTags": BuiltInCategory.OST_LinkAnalyticalTags,
    "MassAreaFaceTags": BuiltInCategory.OST_MassAreaFaceTags,
    "MassTags": BuiltInCategory.OST_MassTags,
    "MaterialTags": BuiltInCategory.OST_MaterialTags,
    "MechanicalEquipmentTags": BuiltInCategory.OST_MechanicalEquipmentTags,
    "MEPSpaceTags": BuiltInCategory.OST_MEPSpaceTags,
    "MultiCategoryTags": BuiltInCategory.OST_MultiCategoryTags,
    "NodeAnalyticalTags": BuiltInCategory.OST_NodeAnalyticalTags,
    "NurseCallDeviceTags": BuiltInCategory.OST_NurseCallDeviceTags,
    "ParkingTags": BuiltInCategory.OST_ParkingTags,
    "PathReinTags": BuiltInCategory.OST_PathReinTags,
    "PipeAccessoryTags": BuiltInCategory.OST_PipeAccessoryTags,
    "PipeFittingTags": BuiltInCategory.OST_PipeFittingTags,
    "PipeInsulationsTags": BuiltInCategory.OST_PipeInsulationsTags,
    "PipeTags": BuiltInCategory.OST_PipeTags,
    "PlantingTags": BuiltInCategory.OST_PlantingTags,
    "PlumbingFixtureTags": BuiltInCategory.OST_PlumbingFixtureTags,
    "PointLoadTags": BuiltInCategory.OST_PointLoadTags,
    "RailingSystemTags": BuiltInCategory.OST_RailingSystemTags,
    "RebarTags": BuiltInCategory.OST_RebarTags,
    "RevisionCloudTags": BuiltInCategory.OST_RevisionCloudTags,
    "RoomTags": BuiltInCategory.OST_RoomTags,
    "SecurityDeviceTags": BuiltInCategory.OST_SecurityDeviceTags,
    "SitePropertyLineSegmentTags": BuiltInCategory.OST_SitePropertyLineSegmentTags,
    "SitePropertyTags": BuiltInCategory.OST_SitePropertyTags,
    "SiteTags": BuiltInCategory.OST_SiteTags,
    "SpanDirectionSymbol": BuiltInCategory.OST_SpanDirectionSymbol,
    "SpecialityEquipmentTags": BuiltInCategory.OST_SpecialityEquipmentTags,
    "SpotCoordinateSymbols": BuiltInCategory.OST_SpotCoordinateSymbols,
    "SpotElevSymbols": BuiltInCategory.OST_SpotElevSymbols,
    "SpotSlopesSymbols": BuiltInCategory.OST_SpotSlopesSymbols,
    "SprinklerTags": BuiltInCategory.OST_SprinklerTags,
    "StairsLandingTags": BuiltInCategory.OST_StairsLandingTags,
    "StairsRunTags": BuiltInCategory.OST_StairsRunTags,
    "StairsSupportTags": BuiltInCategory.OST_StairsSupportTags,
    "StairsTags": BuiltInCategory.OST_StairsTags,
    "StairsTriserTags": BuiltInCategory.OST_StairsTriserTags,
    "StructConnectionTags": BuiltInCategory.OST_StructConnectionTags,
    "StructuralColumnTags": BuiltInCategory.OST_StructuralColumnTags,
    "StructuralConnectionHandlerTags_Deprecated": BuiltInCategory.OST_StructuralConnectionHandlerTags_Deprecated,
    "StructuralFoundationTags": BuiltInCategory.OST_StructuralFoundationTags,
    "StructuralFramingTags": BuiltInCategory.OST_StructuralFramingTags,
    "TelephoneDeviceTags": BuiltInCategory.OST_TelephoneDeviceTags,
    "TrussTags": BuiltInCategory.OST_TrussTags,
    "WallAnalyticalTags": BuiltInCategory.OST_WallAnalyticalTags,
    "WallFoundationAnalyticalTags": BuiltInCategory.OST_WallFoundationAnalyticalTags,
    "WallTags": BuiltInCategory.OST_WallTags,
    "WindowTags": BuiltInCategory.OST_WindowTags,
    "WireTags": BuiltInCategory.OST_WireTags,
}


# def select_tags_by_view(selected_switch):
#     tags_by_view = {}
#
#     cat = switches[selected_switch]
#
#     cl_tags = FilteredElementCollector(doc)
#     tags = cl_tags.OfCategory(cat)
#
#     # Find only current view tags, if not ShiftClick
#     if not __shiftclick__:
#         tags = tags.OwnedByView(doc.ActiveView.Id)
#
#     tags = tags.WhereElementIsNotElementType().ToElements()
#
#     logger.debug(str(len(tags)) + " tags found")
#
#     for e in tags:
#         v = e.OwnerViewId
#         if v not in tags_by_view.keys():
#             tags_by_view[v] = []
#         tags_by_view[v].append(e)
#
#     return tags_by_view


def find_duplicates_on_view(tags, view_name):
    tags_dict = {}

    linked_found = 0

    for tag in tags:
        # try:
        #     # TODO find the way to check tags connected to linked file
        if type(tag) == FamilyInstance:
            continue
        elif type(tag) == RoomTag:
            k = tag.Room.Id
        elif type(tag) == AreaTag:
            k = tag.Area.Id
        else:
            k = tag.TaggedLocalElementId

        # except:
        #     continue

        if k.IntegerValue == -1:
            linked_found += 1
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

    if linked_found:
        logger.warning("View %s has %d tags connected to linked model. They can't be checked" % (
            view_name, linked_found
        ))
    return duplicates_id


def select_duplicate_tags(tags_by_view, selected_switch, all_views):
    duplicates_id = []
    for view, tags in tags_by_view.items():
        view_name = doc.GetElement(view).Name

        duplicates_id_view = find_duplicates_on_view(tags, view_name)
        duplicates_id += duplicates_id_view
        dup_count = len(duplicates_id_view)
        if all_views and dup_count > 0:
            print("View \"%s\": %d of %d tags duplicated" % (
                view_name, dup_count, len(tags) )
                  )

    if pyRevitNewer44:
        selection.set_to(duplicates_id)
    else:
        collection = List[ElementId](duplicates_id)
        selection.SetElementIds(collection)

    print("%d duplicated %s selected" % (len(duplicates_id), selected_switch))


def get_tags_by_type(all_views):
    # find available tags in project
    tags_by_type = {}

    for cat_name, cat in switches.items():
        cl_tags = FilteredElementCollector(doc)
        tags = cl_tags.OfCategory(cat)

        # Find only current view tags, if not ShiftClick
        if not __shiftclick__:
            tags = tags.OwnedByView(doc.ActiveView.Id)

        tags = tags.WhereElementIsNotElementType().ToElements()

        tags = filter(lambda t: type(t) != FamilyInstance, tags)

        if len(tags) == 0:
            continue
        else:
            logger.debug("%d %s found" % (len(tags), cat_name))

            tags_by_view = {}

            for e in tags:
                v = e.OwnerViewId
                if not v:
                    continue

                if v not in tags_by_view.keys():
                    tags_by_view[v] = []
                tags_by_view[v].append(e)

            tags_by_type[cat_name] = tags_by_view

    return tags_by_type


def main(all_views = __shiftclick__):

    # fetching all tags in a project
    tags_by_type = get_tags_by_type(all_views)
    available_types = tags_by_type.keys()
    if len(available_types) == 0:
        if all_views:
            suffix = 'in a project'
        else:
            suffix = 'on active view'
            # TODO ask user to find on all views

        print('No tags found ' + suffix)
        return

    selected_switch = CommandSwitchWindow.show(available_types,
                                               message='Select tag type')
    if selected_switch:
        tags_by_view = tags_by_type[selected_switch]
        select_duplicate_tags(tags_by_view, selected_switch, all_views)


if __name__ == '__main__':
    main()
