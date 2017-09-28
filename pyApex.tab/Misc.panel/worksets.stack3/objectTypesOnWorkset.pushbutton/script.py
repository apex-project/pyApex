__doc__ = 'List all worksets in the model.'

from Autodesk.Revit.DB import Workset, FilteredWorksetCollector, WorksetKind, FilteredElementCollector, ElementWorksetFilter, Element
from Autodesk.Revit.UI import TaskDialog
from pprint import pprint

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

cl = FilteredWorksetCollector(doc)
worksetlist = cl.OfKind(WorksetKind.UserWorkset)

if doc.IsWorkshared:
	for ws in worksetlist:
		elementCollector = FilteredElementCollector(doc).WhereElementIsNotElementType()
		elementWorksetFilter = ElementWorksetFilter(ws.Id, False)
		els = elementCollector.WherePasses(elementWorksetFilter).ToElements()
		print('WORKSET: {0} ID: {1} COUNT: {2}'.format(ws.Name.ljust(50), ws.Id, len(els)))
		els_array = {}

		for e in els:
			t = e.GetType().ToString()
			if t not in els_array.keys():
				els_array[t] = []
			els_array[t].append(str(e.Id))

			# 
		# print(",".join(els_array.keys))
		# print("\n")
		for k in els_array.keys():
			print(k,len(els_array[k]))
			print(",".join(els_array[k]))
		print("\n\n")
else:
	__window__.Close()
	TaskDialog.Show('pyRevit', 'Model is not workshared.')
