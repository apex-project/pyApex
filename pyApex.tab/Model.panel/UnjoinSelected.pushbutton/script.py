# -*- coding: utf-8 -*-
__title__ = 'Unjoin many'
__doc__ = """"""

__helpurl__ = "https://apex-project.github.io/pyApex/help#unjoin-many"

try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr
    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >=4 and PYREVIT_VERSION.minor >=5

if pyRevitNewer44:
    from pyrevit.revit import doc, selection

else:
    from revitutils import doc, selection


from Autodesk.Revit.DB import BuiltInCategory, ElementId, JoinGeometryUtils, Transaction
from Autodesk.Revit.UI import TaskDialog,TaskDialogCommonButtons

selected_ids = selection.element_ids

rng = range(len(selected_ids))
checked_pairs = []
joined_pairs = []
c = 0

for x in rng:
    for y in rng:
        if x == y:
            continue
        _p = sorted([x,y])
        _t = (_p[0],_p[1])
        if _t in checked_pairs:
            continue

        checked_pairs.append(_t)
        eid1 = selected_ids[_p[0]]
        eid2 = selected_ids[_p[1]]
        e1,e2 = doc.GetElement(eid1),doc.GetElement(eid2)
        joined = JoinGeometryUtils.AreElementsJoined(doc,e1,e2)
        if joined:
            joined_pairs.append((e1,e2))

if len(joined_pairs) > 0:
    t = Transaction(doc)
    t.Start(__title__)
    for p in joined_pairs:
        JoinGeometryUtils.UnjoinGeometry(doc,p[0],p[1])
        c+=1
    t.Commit()

TaskDialog.Show(__title__,"%d pairs of elements unjoined" % c)


