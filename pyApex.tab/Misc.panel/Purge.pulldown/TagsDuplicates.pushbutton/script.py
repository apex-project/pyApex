# -*- coding: utf-8 -*- 

__doc__ = 'Select duplicates tags on active view\nShitf+Click - on all views'
__title__ = 'Select duplicate Tags'
import os.path
from pprint import pprint
import time

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ViewType
from Autodesk.Revit.UI import TaskDialog,TaskDialogCommonButtons
from Autodesk.Revit.DB import BuiltInCategory, ElementId
from System.Collections.Generic import List
from Autodesk.Revit.DB import Transaction, TransactionGroup

from Autodesk.Revit.UI import PostableCommand as pc
from Autodesk.Revit.UI import RevitCommandId as rcid
import os

from scriptutils import logger
from scriptutils.userinput import CommandSwitchWindow

# def addtoclipboard(text):
#     command = 'echo ' + text.strip() + '| clip'
#     os.system(command)

#неясно, как реализовать выбор параметра-родителя тэга (tag.Door, tag.Room и т.д.)
switches = {
	"OST_RoomTags": BuiltInCategory.OST_RoomTags,
	"OST_AreaTags": BuiltInCategory.OST_AreaTags,
	"OST_DoorTags": BuiltInCategory.OST_DoorTags,
	"OST_WindowTags": BuiltInCategory.OST_WindowTags,
}
def selectDuplicateTags(selected_switch="OST_RoomTags"):
	uidoc = __revit__.ActiveUIDocument
	doc = __revit__.ActiveUIDocument.Document
	av = doc.ActiveView
	cl_tags = FilteredElementCollector(doc)
	tags = cl_tags.OfCategory(switches[selected_switch]).WhereElementIsNotElementType().ToElementIds()
	logger.debug(str(len(tags)) + " tags found")
	tags_dict = {}
	views_dict = []
	for eId in tags:
		e = doc.GetElement(eId)
		try:
			e.View
		except:
			logger.debug(str(eId) + " is element type")
			continue
		try:

			v = e.View
			#пропускает, если тэг не на текущем виде - оптимизировать через фильтр!
			if not __shiftclick__ and v.Id != av.Id:
				logger.debug(str(eId) + " not on active view" + v.Name)
				continue

			text = str(e.Room.Id) + "_" + str(v.Id)
			views_dict.append(int(str(e.View.Id)))
			if text not in tags_dict:
				tags_dict[text] = []
			tags_dict[text].append(int(eId.ToString()))
		except:
			logger.info(str(eId) + " unknown exception")

	ttags = []
	for t in tags_dict:
		if len(tags_dict[t])>1:
			i = 0
			tags_dict[t].sort()
			for tt in tags_dict[t]:
				if i!=0:                
					ttags.append(tt)
				i+=1

	ttags_text = ",".join( map(lambda x: str(x),ttags) )

	selection = uidoc.Selection
	collection = List[ElementId](map(lambda x: ElementId(int(x)),ttags))

	selection.SetElementIds(collection)
	logger.info(str(len(ttags)) + " tags selected")

# selected_switch = CommandSwitchWindow(sorted(switches.keys()), 'Pick only elements of type:').pick_cmd_switch()
# if selected_switch is not '':
selectDuplicateTags()
# else:
# 	TaskDialog.Show(__title__,"Ошибка при выборе категории")
if not __forceddebugmode__:
	__window__.Close()