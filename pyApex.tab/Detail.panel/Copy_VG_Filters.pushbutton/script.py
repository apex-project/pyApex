# -*- coding: utf-8 -*- 
__doc__ = 'Lists all the sheets in the project.'
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
from scriptutils import logger
import clr
import os
import os.path as op
import pickle as pl

app = __revit__.Application.Documents
uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
selection = uidoc.Selection.GetElementIds()

from scriptutils.userinput import SelectFromList,SelectFromCheckBoxes

class CheckBoxOption:
    def __init__(self, name, default_state=False):
        self.name = name
        self.state = default_state

    # define the __nonzero__ method so you can use your objects in an 
    # if statement. e.g. if checkbox_option:
    def __nonzero__(self):
        return self.state

    # __bool__ is same as __nonzero__ but is for python 3 compatibility
    def __bool__(self):
        return self.state

app = __revit__.Application.Documents
uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

usertemp = os.getenv('Temp')
prjname = op.splitext(op.basename(doc.PathName))[0]

datafile = usertemp + '\\' + prjname + '_pyChecked_Templates.pym'
logger.info(datafile)

selset = []
def main():
    allowed_types = [
        ViewPlan,
        View3D,
        ViewSection,
        ViewSheet,
        ViewDrafting
    ]

    selection = uidoc.Selection.GetElementIds()
    if type(doc.ActiveView)!=View:
        active_view = doc.ActiveView
    else:
        active_view = doc.GetElement(selection[0])
        if type(active_view) not in allowed_types:
            logger.error('Selected view is not allowed. Please select or open view from which you want to copy template settings VG Overrides - Filters')
            return
    logger.info('Source view selected: %s id%s' % (active_view.Name, active_view.Id.ToString()))
    active_template = doc.GetElement(active_view.ViewTemplateId)
    logger.info('Source template: %s id%s' % (active_template.Name, active_template.Id.ToString()))

    active_template_filters = active_template.GetFilters()
    
    # print(active_template_filter_rules)
    # return

    selset = read_states()
    # print(selset)
    vt_dict = get_view_templates(doc,selset=selset)
    active_template_filters_ch = get_view_filters(doc,active_template)

    all_checkboxes = SelectFromCheckBoxes.show(active_template_filters_ch)
    sel_checkboxes_filter = []
    # now you can check the state of checkboxes in your program
    for checkbox in all_checkboxes:
        if checkbox:
            sel_checkboxes_filter.append(checkbox)
    if len(sel_checkboxes_filter)==0:
        return


    all_checkboxes = SelectFromCheckBoxes.show(vt_dict)
    sel_checkboxes = []
    # now you can check the state of checkboxes in your program
    for checkbox in all_checkboxes:
        if checkbox:
            sel_checkboxes.append(checkbox)
    if len(sel_checkboxes)==0:
        return
    write_state(sel_checkboxes)


    t = Transaction(doc)
    t.Start("Copy VG")

    for ch in sel_checkboxes:
        vt = doc.GetElement(ch.id)

        if vt.Id == active_template.Id:
            print('current template found')
            continue

        for f in sel_checkboxes_filter:
            fId = f.id
            try:
                vt.RemoveFilter(fId)
                logger.info('filter %s deleted from template %s' % (fId.ToString(), vt.Name))
            except:
                pass
            try:
                fr = active_template.GetFilterOverrides(fId)
                vt.SetFilterOverrides(fId,fr)
            except Exception as e:
                logger.warning('filter not aplied to active view %s\n%s' % (fId.ToString(), e))
    t.Commit()
    print("finished")

def read_states():
    try:
        f = open(datafile, 'r')
        cursel = pl.load(f)
        f.close()

        selset = []
        for elId in cursel:
            selset.append(int(elId))

        return selset
    except:

        return []


def write_state(checkboxes):
    selection = {c.id.ToString() for c in checkboxes}
    f = open(datafile, 'w')
    pl.dump(selection, f)
    f.close()

class CheckBoxOption:
    def __init__(self, name,id, selset=[], default_state=False):
        self.name = name
        self.id = id

        self.state = default_state
        # print(selset)
        # print(self.id.ToString, True)
        if int(self.id.ToString()) in selset:
            # print(self.id.ToString, True)
            self.state = True
        
        

    # define the __nonzero__ method so you can use your objects in an 
    # if statement. e.g. if checkbox_option:
    def __nonzero__(self):
        return self.state

    # __bool__ is same as __nonzero__ but is for python 3 compatibility
    def __bool__(self):
        return self.state

def get_filter_rules(doc):
    cl = FilteredElementCollector(doc).WhereElementIsNotElementType()
    els = cl.OfClass(type(ElementInstance)).ToElementIds()    
    return els

def get_view_templates(doc, view_type=None,selset=selset):
    cl_view_templates = FilteredElementCollector(doc).WhereElementIsNotElementType()
    allview_templates = cl_view_templates.OfCategory(BuiltInCategory.OST_Views).ToElementIds()
    vt_dict = []
    for vtId in allview_templates:
        vt = doc.GetElement(vtId)
        if vt.IsTemplate:
            if view_type == None or vt.ViewType == view_type:
                vt_dict.append(CheckBoxOption(vt.Name,vtId,selset))
    return vt_dict

def get_view_filters(doc,v):
    dct = []
    ftrs = v.GetFilters()
    for fId in ftrs:
        f = doc.GetElement(fId)
        dct.append(CheckBoxOption(f.Name,fId))
    return dct
if __name__ == "__main__":
    main()


# for doc1 in __revit__.Application.Documents:
#     if doc.Title != doc1.Title and doc1.IsLinked==False:
#         src_doc = doc1
#         break

# print(doc.Title + " <-- " + src_doc.Title)
# l = []
# d = {}

# e = 0


# t = Transaction(doc)
# t.Start("CopyBetweenDocs")

# for s in selection:
#     # todo: search for use of .Parameter[] indexer.
#     # v = doc.GetElement(s)
#     # try:
        
#     #     v_src = doc.GetElement(s)
#     # except:
#     #     logger.warning('id%s not found in %s' % (str(s), src_doc.Title, ))
#     #     continue
#     # if type(v) != IndependentTag:
#     #     logger.warning('Selected id%s is not IndependentTag' % str(s))
#     #     continue
#     # if type(v_src) != IndependentTag:
#     #     logger.warning('Source id%s is not IndependentTag' % str(s))
#     #     continue

#     # print(v.TaggedElementId)
#     # src_link_instance_id = v_src.TaggedElementId.LinkInstanceId
#     # src_linked_element_id = v_src.TaggedElementId.LinkedElementId
#     # print(type(v.TaggedElementId) == LinkElementId, v.TaggedElementId.LinkInstanceId, type(v.TaggedElementId.LinkInstanceId), v.TaggedElementId.LinkedElementId, type(v.TaggedElementId.LinkedElementId))
#     # instance = LinkElementId(src_link_instance_id,src_linked_element_id)
#     # # v.TaggedElementId.LinkInstanceId = v_src.TaggedElementId.LinkInstanceId
#     # # v.TaggedElementId.LinkedElementId = v_src.TaggedElementId.LinkedElementId

# t.Commit()
# print("finished")
# view = clr.Reference[View]()

# t = Transaction(src_doc)
# t.Start("CopyBetweenDocs")

# for vId in d.keys():
#   print(str(vId),len(d[vId]))
#   # print(",".join(d[vId]))
#   sView = doc.GetElement(vId)
#   copyId = d[vId]
#   element_collection = List[ElementId](copyId)
#   tView = src_doc.GetElement(vId)
#   for ecopy in ElementTransformUtils.CopyElements.Overloads:
#       try:
#           copiedId = ecopy(sView,copyId,tView,None,CopyPasteOptions())
#       except:
#           continue
#   print("Copied " + str(len(copiedId)))

# t.Commit()
# print("finished")