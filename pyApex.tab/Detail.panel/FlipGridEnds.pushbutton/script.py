# -*- coding: utf-8 -*-
__title__ = 'Flip\nGrid Ends'
__doc__ = """Flip visibility of bubbles at the ends of selected grids. If both bubbles were visible ony one lefts.

Переключает отображения кружочков для выделенных осей. Если у оси были видимы оба кружочка, будет отображаться только один"""

__helpurl__ = "https://apex-project.github.io/pyApex/help#flip-grid-ends"

try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr
    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >=4 and PYREVIT_VERSION.minor >=5

if pyRevitNewer44:
    from pyrevit import script, revit
    output = script.get_output()
    logger = script.get_logger()
    linkify = output.linkify
    doc = revit.doc
    uidoc = revit.uidoc
    selection = revit.get_selection()
else:
    from scriptutils import logger, this_script
    from revitutils import doc, selection, uidoc

    output = this_script.output


from Autodesk.Revit.DB import Grid, DatumEnds, Transaction
from Autodesk.Revit import UI
from Autodesk.Revit.UI import TaskDialog

class PickByCategorySelectionFilter(UI.Selection.ISelectionFilter):
    def __init__(self, catname):
        self.category = catname

    # standard API override function
    def AllowElement(self, element):
        if self.category in element.Category.Name:
            return True
        else:
            return False

    # standard API override function
    def AllowReference(self, refer, point):
        return False


def pickbycategory(catname):
    msfilter = PickByCategorySelectionFilter(catname)
    selection_list = revit.pick_rectangle(pick_filter=msfilter)
    return selection_list


def get_selected_grids():
    sel = selection.elements
    sel = filter(lambda x: type(x) == Grid, sel)

    if len(sel) == 0:
        TaskDialog.Show(__title__, "Select Grids to flip bubbles visibility")
        sel = pickbycategory("Grid")
        if not sel:
            return

    return list(sel)


def flip_grid(grid, view):
    if not grid.CanBeVisibleInView(view):
        return

    ends = [
        DatumEnds.End0,
        DatumEnds.End1
    ]
    last = None
    changed = 0
    for end in ends:
        if grid.IsBubbleVisibleInView(end, view) and not last:
            grid.HideBubbleInView(end, view)
            last = True
            changed += 1
        else:
            if not grid.IsBubbleVisibleInView(end, view):
                grid.ShowBubbleInView(end, view)
                changed += 1

    return bool(changed)


def main():
    sel_grids = get_selected_grids()
    if not sel_grids:
        return
    active_view = doc.ActiveView

    changed = 0
    t = Transaction(doc)
    t.Start(__title__)

    for g in sel_grids:
        changed += bool( flip_grid(g, active_view) )

    if changed > 0:
        t.Commit()
    else:
        t.Rollback()

    if changed != len(sel_grids):
        TaskDialog.Show(__title__, "%d of %d grids were flipped" % (changed, len(sel_grids)))
    elif changed == 0:
        TaskDialog.Show(__title__, "Nothing flipped")

if __name__ == '__main__':
    main()