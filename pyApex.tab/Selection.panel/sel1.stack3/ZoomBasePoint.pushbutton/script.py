import os.path
from pprint import pprint
import time
import itertools

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ViewType, ElementCategoryFilter
from Autodesk.Revit.UI import TaskDialog,TaskDialogCommonButtons
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType
from Autodesk.Revit.DB import BuiltInCategory, ElementId, XYZ, ElementTransformUtils
from System.Collections.Generic import List
from Autodesk.Revit.DB import Transaction, TransactionGroup

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
doc_info = doc.ProjectInformation
ppath = doc.PathName
pfilename = os.path.splitext(os.path.split(ppath)[1])[0]

dir_path = os.path.dirname(os.path.realpath(__file__))
#dir_path = os.path.dirname(ppath)



cl_all = FilteredElementCollector(doc).WhereElementIsNotElementType()
# basepoint2 = ElementCategoryFilter(BuiltInCategory.OST_ProjectBasePoint, True)
basepoint = cl_all.OfCategory(BuiltInCategory.OST_ProjectBasePoint).ToElementIds()

uidoc.ShowElements(basepoint[0])