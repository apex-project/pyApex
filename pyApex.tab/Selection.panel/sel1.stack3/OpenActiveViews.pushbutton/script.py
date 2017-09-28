'Opens selected views'
__title__ = 'Open Views'

__window__.Close()
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

sel = uidoc.Selection.GetElementIds()
i = 0
for elId in sel:
	uidoc.ActiveView = doc.GetElement(elId)