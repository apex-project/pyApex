# -*- coding: utf-8 -*-
__title__ = 'Copy btw. Docs'
__doc__ = """Copy selection from active document to another opened document.
In case of geometry it uses origin-to-origin alignment
Context: elements should be selected

Копирует выбранные элементы из активного документа в другой открытй документ
При копировании геометрии используется выравнивание по нулю проекта
Контекст: необходимо выбрать элементы для копирования"""
__context__ = 'Selection'

from pyrevit import script, revit, forms
from Autodesk.Revit.DB import Transaction, Transform, ElementId, ElementTransformUtils, FilteredElementCollector, BuiltInCategory
from Autodesk.Revit.DB.Architecture import *
import clr
clr.AddReference("System")
from System.Collections.Generic import List

logger = script.get_logger()

def run(sel, location_option):
    logger.info("Location option: %s " % location_option)
    docs = __revit__.Application.Documents
    # where to copy
    src_doc = __revit__.ActiveUIDocument.Document
    docs = filter(lambda d: not d.IsLinked and d != src_doc, docs)
    trg_docs = forms.SelectFromList.show(docs, name_attr='Title', title='Documents to paste selection',
                                          button_name='Paste', multiselect=True)
    null_point_src = None
    null_point_cat = None
    if location_option == "Project Base Point":
        null_point_cat = BuiltInCategory.OST_SharedBasePoint
    elif location_option == "Shared Site Point":
        null_point_cat = BuiltInCategory.OST_ProjectBasePoint

    if null_point_cat:
        null_point_src = FilteredElementCollector(src_doc).WhereElementIsNotElementType().OfCategory(null_point_cat).WhereElementIsNotElementType().ToElements()
        if len(null_point_src) == 0:
            logger.warning("Point for location option wasn't found in source document. Default alignment will be used")

    for trg_doc in trg_docs:
        logger.debug(trg_doc)
        logger.debug(len(trg_doc.Title))
        s = "Copy %d elements from %s to %s" % (len(sel), src_doc.Title, trg_doc.Title)
        print(s)
        # logger.info(s) # TODO Fix - cannot log cyrylic project name

        # Transform
        transform_vector = None
        if null_point_src:
            null_point_trg = FilteredElementCollector(trg_doc).WhereElementIsNotElementType().OfCategory(
                null_point_cat).WhereElementIsNotElementType().ToElements()
            if len(null_point_trg) == 0:
                logger.warning(
                    "Point for location option wasn't found in target document. Document will be skipped")
                continue
            # _transform_vector = null_point_trg[0].GetTransform().BasisX - null_point_src[0].GetTransform().BasisX
            print(null_point_trg[0].BoundingBox[null_point_trg[0]])
            transform_vector = Transform.CreateTranslation(null_point_trg[0].BoundingBox.Min - null_point_src[0].BoundingBox.Min)

        t = Transaction(trg_doc, __title__ + " - %d elements from %s" % (len(sel), src_doc.Title))
        t.Start()
        try:
            ElementTransformUtils.CopyElements(src_doc, List[ElementId](sel), trg_doc, transform_vector, None)
            t.Commit()
        except Exception as exc:
            t.RollBack()
            logger.error(exc)

def have_location(elements):
    for e in elements:
        if getattr(e, "Location"):
            return True
    return False

def get_locaton_option():
    options = [
        "Document null",
        "Project Base Point",
        "Shared Site Point"
    ]
    return forms.SelectFromList.show(options, title='Select alignment type', button_name='Continue')

if __name__ == '__main__':
    sel_elements = revit.get_selection().elements
    location_option = None

    # TODO select location type
    # TODO align by view (if not exist?)
    # if have_location(sel_elements):
    #     location_option = get_locaton_option()
    #     if not location_option:
    #         forms.alert("Nothing selected. Default align will be used")

    sel = revit.get_selection().element_ids
    if not sel:
        forms.alert("Nothing selected")
    else:
        run(sel, location_option)
