# -*- coding: utf-8 -*-
__title__ = 'Zoom Base Point'
__doc__ = """Zoom in active view to Project base point. If it's hidden - enables "Reveal Hidden" mode.
Shift+Click - to Site point

Находит базовую точку проекта на текущем виде. Если точка скрыта - включает режим показа скрытых объектов.
Shift+Click - Точку съемки"""

__helpurl__ = "https://apex-project.github.io/pyApex/help#zoom-base-point"


import os.path
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ElementId, Transaction

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

cl = FilteredElementCollector(doc, uidoc.ActiveView.Id).WhereElementIsNotElementType()

if __shiftclick__:
    category = BuiltInCategory.OST_SharedBasePoint
else:
    category = BuiltInCategory.OST_ProjectBasePoint

elements = cl.OfCategory(category).ToElementIds()

if len(elements)==0:
    t = Transaction(doc, "[%s] Reveal hidden" % __title__)
    t.Start()
    uidoc.ActiveView.EnableRevealHiddenMode()
    t.Commit()
    cl = FilteredElementCollector(doc).WhereElementIsNotElementType()
    elements = cl.OfCategory(category).ToElementIds()

uidoc.ShowElements(elements[0])