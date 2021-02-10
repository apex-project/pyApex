# -*- coding: utf-8 -*-
__doc__ = """Create DWG link and orient it to Shared Site Point. As if this DWG had shared coordinates.
Useful for placing General Plan dwg files with absolute coordinates.
Shift+Click - enable/disable rotation manually

Создает DWG связь и размещает ее в Точке Съемки проекта. Как если бы dwg имел общие координаты с моделью.
Удобно при создании связи с dwg-файлами генплана.
Shift+Click - включить или выключить поворот вручную
"""

__title__ = 'Link DWG by Site'

__helpurl__ = "https://apex-project.github.io/pyApex/help#link-dwg-site"

import clr
import System
clr.AddReference('System')

try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr

    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >= 4 and PYREVIT_VERSION.minor >= 5

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons

if pyRevitNewer44:
    from pyrevit import script
    from pyrevit.forms import pick_file
    logger = script.get_logger()
    from pyrevit.revit import doc, selection, uidoc

    selection = selection.get_selection()
    my_config = script.get_config()
else:
    forms = None
    from scriptutils import logger
    from scriptutils.userinput import pick_file
    from scriptutils import this_script as script
    from revitutils import doc, selection, uidoc

    my_config = script.config


def main():
    location = doc.ActiveProjectLocation
    activeview = uidoc.ActiveView
    project_position = location.get_ProjectPosition(XYZ.Zero)
    project_angle = project_position.Angle

    origin = location.GetTotalTransform().Origin

    # Search for any 3D view or a Plan view
    cl = FilteredElementCollector(doc)
    views = cl.OfCategory(BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()

    q = TaskDialog.Show(__title__, "Link CAD to current view only?",
                        TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No | TaskDialogCommonButtons.Cancel)
    if str(q) == "No":
        this_view_only = False
        target_view = None
    elif str(q) == "Yes":
        this_view_only = True
        target_view = activeview
    else:
        return

    rotate = False
    if not target_view:
        target_view_project = None
        target_view_3d = None

        for v in views:
            if v.IsTemplate:
                continue

            if type(v) == ViewPlan:
                orientation = v.get_Parameter(BuiltInParameter.PLAN_VIEW_NORTH)
                if orientation.AsInteger() == 1:
                    target_view = v
                    break
                else:
                    if not target_view_project:
                        target_view_project = v

            if type(v) == View3D and not target_view_3d:
                target_view_3d = v

        if not target_view:
            rotate = True
            if target_view_project:
                target_view = target_view_project
            elif target_view_3d:
                target_view = target_view_3d

    if not target_view:
        logger.error("Please create 3D view or a PlanView in a project to place CAD correctly")
        return

    path = pick_file(files_filter="DWG files (*.dwg)|*.dwg|DXF files (*.dxf)|*.dxf|DGN files (*.dgn)|*.dgn|All files (*.*)|*.*")

    if not path:
        return

    o = DWGImportOptions()
    o.AutoCorrectAlmostVHLines = False
    o.Unit = ImportUnit.Meter
    o.OrientToView = False
    o.ReferencePoint = origin
    o.ThisViewOnly = this_view_only

    link_func = doc.Link.Overloads[str, DWGImportOptions, View, System.Type.MakeByRefType(ElementId)]

    t = Transaction(doc)
    t.Start(__title__)
    try:
        status, e_id = link_func(path, o, target_view, )
    except Exception as e:
        logger.error("Unable to import CAD")
        logger.error(e)
        status = False

    # override rotation option
    if __shiftclick__:
        q = TaskDialog.Show(__title__, "Is it okay?\nIf not CAD will be rotated",
                                TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No | TaskDialogCommonButtons.Cancel)
        if str(q) == "No":
            rotate = True
        elif str(q) == "Yes":
            rotate = False
        else:
            return

    if status:
        l = doc.GetElement(e_id)
        if rotate:
            if l.Pinned:
                l.Pinned = False
            axis = Line.CreateBound(origin,
                                    XYZ(origin.X, origin.Y, origin.Z + 1))

            ElementTransformUtils.RotateElement(doc, l.Id, axis, -project_angle)
        l.Pinned = True
        t.Commit()
    else:
        t.RollBack()

if __name__ == '__main__':
    main()

