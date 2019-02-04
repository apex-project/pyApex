# -*- coding: utf-8 -*-
__title__ = 'Copy btw. Docs'
__doc__ = """Copy selection from active document to another opened document.
In case of geometry it uses origin-to-origin alignment

Копирует выбранные элементы из активного документа в другой открытй документ
При копировании геометрии используется выравнивание по нулю проекта"""


from pyrevit import script, revit, forms
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
from Autodesk.Revit.DB import Transaction, Transform, ElementId, CopyPasteOptions, FilteredElementCollector, BuiltInCategory, BuiltInParameter, ElementTransformUtils
from Autodesk.Revit.DB.Architecture import *
import clr
clr.AddReference("System")
from System.Collections.Generic import List

logger = script.get_logger()

def run(sel):
    docs = __revit__.Application.Documents
    # where to copy
    src_doc = __revit__.ActiveUIDocument.Document
    docs = filter(lambda d: not d.IsLinked and d != src_doc, docs)
    trg_docs = forms.SelectFromList.show(docs, name_attr='Title', title='Documents to paste selection',
                                          button_name='Paste', multiselect=True)
    for trg_doc in trg_docs:
        logger.debug(trg_doc)
        logger.info("Copy %d elements from %s to %s" % (len(sel), src_doc.Title, trg_doc.Title))
        t = Transaction(trg_doc, __title__ + " - %d elements from %s" % (len(sel), src_doc.Title))
        t.Start()
        try:
            ElementTransformUtils.CopyElements(src_doc, List[ElementId](sel), trg_doc, None, None)
            t.Commit()
        except Exception as exc:
            t.RollBack()
            logger.error(exc)

if __name__ == '__main__':
    sel = revit.get_selection().element_ids
    if not sel:
        forms.alert("Nothing selected")
    else:
        run(sel)
