# -*- coding: utf-8 -*-

__title__ = 'Purge\nfamilies'
__doc__ = """Opens each family in active document, then delete unused elements and load back to source document.
Works recursively until the lowest level of embeded families.
Click+Shift - check only the highest embeded level

Открывает каждое семейство в модели, удаляет неиспользуемые элементы и загружает обратно в модель.
Работает рекурсивно, опускаясь до самого глубокого уровня вложенных семейств.
Click+Shift  - проверять только верхний уровень вложенности

Available cleaners:
- families
- material
- image types
- fill patterns
- line patterns
"""

__helpurl__ = "https://apex-project.github.io/pyApex/help#purge-families"

try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr
    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >=4 and PYREVIT_VERSION.minor >=5

if pyRevitNewer44:
    from pyrevit import script, revit
    from pyrevit.revit import doc
    from pyrevit.forms import SelectFromList, SelectFromCheckBoxes
    output = script.get_output()
    logger = script.get_logger()
    linkify = output.linkify
    selection = revit.get_selection()

else:
    from scriptutils import logger, this_script as script
    from revitutils import doc, selection
    from scriptutils.userinput import SelectFromList, SelectFromCheckBoxes
    output = script.output

window_title = __title__.replace("\n", " ")
output.set_title(window_title)

import csv
import os
import types
import locale
import clr
import time
import math

from pprint import pprint
from datetime import datetime

from Autodesk.Revit.UI import PostableCommand,TaskDialog, TaskDialogCommonButtons
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import *


PURGE_NOTUSED_FAMILIES = False
PURGE_DIR = "D:\\99_PURGE"

# Set windows locale. Locale is used for put necessary decimal separator in CSV
locale.setlocale(locale.LC_ALL, '')

# Fetch available BuiltInCategories. Used for select builtincategory by id.
BUILTINCATEGORIES_DICT = {}
for c in BuiltInCategory.GetValues(BuiltInCategory):
    BUILTINCATEGORIES_DICT[int(c)] = c

PURGE_RESULTS_CSV = []
START_TIME = None


def invert_dict_of_lists(d):
    """
    Flip dictionary.

    Args:
        d: Source dict

    Returns:
        result: Flipped dict
    """
    result = {}
    for k in d.keys():
        l = d[k]
        for e in l:
            if e not in result.keys():
                result[e] = []
            result[e].append(k)
    return result


def dependencies_find(document, element, result=None):
    """
    Find all elements of which specified element is dependent.
    Находит все элементы в документе, от которых зависит указанный элемент.

    Args:
        document: Active document
        element: Element for which is needed to find dependencies
        result: List of element ids (IntegerValues). New ids will be appended to the list.

    Returns:
        result: Source list + new element ids
    """
    params = element.Parameters

    if not result:
        result = []

    for p in params:
        if not p.HasValue:
            continue
        if p.StorageType != StorageType.ElementId:
            continue

        e_id_child = p.AsElementId().IntegerValue
        if e_id_child > 0:

            result.append(e_id_child)
            e_child = document.GetElement(p.AsElementId())

            if e_child.GetType() == FamilySymbol or e_child.GetType() == AnnotationSymbolType:
                # print("Family symbol", e_child.Family.Id)
                f_id = e_child.Family.Id
                if f_id:
                    result.append(f_id.IntegerValue)

    try:
        e_type_id = element.GetTypeId()
        if e_type_id:
            result.append(e_type_id.IntegerValue)
    except Exception as e:
        pass
    try:
        line_style = element.LineStyle
        if line_style:
            bprint("\t\tLineStyle " + str(line_style.Id.IntegerValue))
            result.append(line_style.Id.IntegerValue)
    except Exception as e:
        pass

    return result


def dependencies_structure(document):
    """
    Find dependencies between elements in specified Document. Result is the dictionary with keys
    "Element of which dependent" and lists "Elements which are dependent"

    Находит зависимости между элементами в документе. На выходе - словарь с ключами "Элемент от которого зависят"
    и списком "Элементы которые зависят".

    Args:
        document: Document to search

    Returns:
        (Deprecated) result_inv: Dependencies dict.
            Dictionary<int(ElementId of which dependent)> = List<int(ElementId dependent of the first eId)>

        result_inv_list: List of element ids (int) of which other elements are dependent
    """

    global BUILTINCATEGORIES_DICT
    result = {}

    # Collect all elements in document
    coll1 = FilteredElementCollector(document).WhereElementIsNotElementType()
    elements = list(coll1.ToElements())
    coll2 = FilteredElementCollector(document).WhereElementIsElementType()
    elements += list(coll2.ToElements())

    # Find dependencies for each element and add it to result dict <Element> = List<Of which dependent>
    for e in elements:
        e_id = e.Id.IntegerValue

        childs = dependencies_find(document, e)
        if len(childs) > 0:
            if e_id not in result.keys():
                result[e_id] = []
            result[e_id] += childs

    # Flip the dict so the structure will be <Of which dependent> = List<Which are dependent>
    result_inv = invert_dict_of_lists(result)
    result_inv.pop(-1, None)
    result_inv_list = set(result_inv.keys())

    """
    For cases, where not used elements are necessary for Types.
    E.g. in Window or Door family you can select different embed families of handle

    If family type (Generic model, Special equipment etc.) is specified as one of types parameters
    all not used elements of this type will be treated as used and will appears in result of definition.
    """
    if not document.IsFamilyDocument:  # types can be only in FamilyDocument
        mgr = document.FamilyManager
        params = mgr.Parameters

        # Creates list of parameters with type "Family"
        params_family = []
        for p in params:
            if p.Definition.ParameterType == ParameterType.FamilyType:
                params_family.append(p)

        # It is possible to get BuiltInCategory of parameter only from it value.
        # Iterate through all the types while not empty parameter will be found to get Category of it.
        document_types = mgr.Types
        params_family_found = []
        params_family_categories = []
        for t in document_types:
            for p in params_family:
                if p in params_family_found:  # skip if this parameter already found
                    continue
                if not t.HasValue(p):  # skip if parameter is empty
                    continue
                eid = t.AsElementId(p)
                param_family_type = document.GetElement(eid)
                param_family_category = BUILTINCATEGORIES_DICT[param_family_type.Category.Id.IntegerValue]

                if param_family_category:
                    params_family_categories.append(param_family_category)

                params_family_found.append(p)

        # Select elements of each of found categories and append ids to final list
        for c in params_family_categories:
            category_els = FilteredElementCollector(document).OfCategory(c).WhereElementIsElementType().ToElements()
            category_els = filter(lambda x: type(x) == FamilySymbol or type(x) == AnnotationSymbolType,
                                  category_els)
            category_els_ids = map(lambda x: x.Family.Id.IntegerValue, category_els)

            result_inv = result_inv.union(category_els_ids)

    return result_inv_list


class FamilyLoadOption(IFamilyLoadOptions):
    def __init__(self): pass

    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues = True
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        return True


def filter_nonetypes(doc, ids):
    result = []
    for e_id in ids:
        if doc.GetElement(e_id) != None:
            result.append(e_id)
            print(doc.GetElement(e_id).GetType())
    return result


def get_families(doc):
    cl = FilteredElementCollector(doc)

    families_types = set(cl.WhereElementIsElementType().ToElements())
    families = {}
    for f in families_types:
        if type(f) == FamilySymbol or type(f) == AnnotationSymbolType:
            ff = f.Family
            f_id = int(ff.Id.IntegerValue)
            if f_id not in families.keys():
                families[f_id] = 0
            families[f_id] += len(get_familysymbol_instances(doc, f))

    used = list(filter(lambda x: families[x] != 0, families.keys()))
    not_used = list(filter(lambda x: families[x] == 0, families.keys()))

    used = list(map(lambda x: doc.GetElement(ElementId(x)), used))
    not_used = list(map(lambda x: doc.GetElement(ElementId(x)), not_used))

    return used, not_used


def get_materials(doc):
    cl = FilteredElementCollector(doc)
    materials = set(cl.OfCategory(BuiltInCategory.OST_Materials).WhereElementIsNotElementType().ToElements())

    return materials


def get_FillPatterns(doc):
    cl = FilteredElementCollector(doc)
    fillpatterns = set(cl.OfClass(clr.GetClrType(FillPatternElement)).ToElements())

    return fillpatterns


def get_LinePatterns(doc):
    cl = FilteredElementCollector(doc)
    elements = set(cl.OfClass(clr.GetClrType(LinePatternElement)).ToElements())

    return elements


def get_ImageType(doc):
    cl = FilteredElementCollector(doc)
    imagetype = set(cl.OfClass(ImageType).ToElements())

    return imagetype


def get_Lines(doc):
    c = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Lines)
    # print(c, type(c))
    subcats = c.SubCategories

    return subcats


class Purgers(object):
    def __init__(self):
        pass

    # def _purge(self, doc, purger_name, **kwargs):
    #
    #
    def Families(self, doc, deps, **kwargs):
        if "fam_not_used" not in kwargs.keys():
            return

        doc_families = kwargs["fam_not_used"]
        # print(doc_families)


        not_purged = []
        count = 0

        for f in doc_families:
            # print("\n" + f.Name)

            if f.IsInPlace:
                continue
            try:
                ids = doc.Delete(f.Id)
                count += 1
            except Exception as e:
                not_purged.append(f)

        return (count, len(doc_families), not_purged)

    def Materials_wip(self, doc, deps, **kwargs):
        # TODO проверять object styles
        materials = get_materials(doc)

        not_purged = []
        count = 0
        mcount = len(materials)
        for e in materials:
            if e.Id.IntegerValue in deps:
                mcount -= 1
                continue

            try:
                ids = doc.Delete(e.Id)
                # print(len(ids))
                count += 1
            except Exception as exception:
                print("exception4", exception)
                not_purged.append(e)
                pass

        return (count, mcount, not_purged)

    def FillPatterns_wip(self, doc, deps, **kwargs):
        elements = get_FillPatterns(doc)

        not_purged = []
        count = 0
        mcount = len(elements)
        for e in elements:
            if e.Id.IntegerValue in deps:
                mcount -= 1
                continue

            try:
                ids = doc.Delete(e.Id)
                # print(len(ids))
                count += 1
            except Exception as exception:
                # print("exception6", exception, e.Id.IntegerValue)
                not_purged.append(e)
                pass

        return (count, mcount, not_purged)

    def LinePatterns_wip(self, doc, deps, **kwargs):
        #TODO проверять object styles
        elements = get_LinePatterns(doc)

        not_purged = []
        count = 0
        mcount = len(elements)
        for e in elements:
            if e.Id.IntegerValue in deps:
                mcount -= 1
                continue

            try:
                ids = doc.Delete(e.Id)
                # print(len(ids))
                count += 1
            except Exception as exception:
                # print("exception6", exception, e.Id.IntegerValue)
                not_purged.append(e)
                pass

        return (count, mcount, not_purged)

    def ImageType(self, doc, deps, **kwargs):
        elements = get_ImageType(doc)

        not_purged = []
        count = 0
        mcount = len(elements)

        for e in elements:
            if e.Id.IntegerValue in deps:
                mcount -= 1
                continue

            try:
                ids = doc.Delete(e.Id)
                # print(len(ids))
                count += 1
            except Exception as exception:
                print("exception0", exception)
                not_purged.append(e)
                pass

        return (count, mcount, not_purged)

    def _Lines(self, doc, deps, **kwargs):
        elements = get_Lines(doc)

        not_purged = []
        count = 0
        mcount = len(elements)

        for e in elements:
            if e.Id.IntegerValue in deps:
                mcount -= 1
                continue

            try:
                ids = doc.Delete(e.Id)
                # print(len(ids))
                count += 1
            except Exception as exception:
                print("exception1", exception)
                not_purged.append(e)
                pass

        return (count, mcount, not_purged)

    def _PostCommand(self, doc):
        __revit__.PostCommand(PostableCommand.PurgeUnused)
        return

    def _template(self, doc, **kwargs):
        """
        fetch elements
        copy list to deleted
        for e in elements:

            check element

            try to delete
                count ++
            catch:
                not_purged.append(

        """
        return ("count deleted -> int", "count found -> ", "not_purged -> list of elements")



def write_csv(path, data=None, separator=";", encoding="windows-1251"):
    global PURGE_RESULTS_CSV
    if not data:
        data = PURGE_RESULTS_CSV

    lines = []

    for l in data:
        l = map(lambda x: str(x), l)
        ll = separator.join(l)
        lines.append(ll.encode(encoding, 'ignore'))

    with open(path + ".csv", "w") as f:
        f.write('\n'.join(lines))




def get_familysymbol_instances(doc, fi):
    cl = FilteredElementCollector(doc)

    fifilter = FamilyInstanceFilter(doc, fi.Id)
    instances = set(cl.WhereElementIsNotElementType().WherePasses(fifilter).ToElements())

    # for catching cases where LegendComponent for the family is placed
    cl2 = FilteredElementCollector(doc)
    legends = cl2.WhereElementIsNotElementType().OfCategory(BuiltInCategory.OST_LegendComponents).ToElements()
    for e in legends:

        p = e.get_Parameter(BuiltInParameter.LEGEND_COMPONENT)
        fs_id = p.AsElementId()
        if fs_id.IntegerValue > 0:
            fs = doc.GetElement(fs_id)
            try:
                ff = fs.Family

                # check is legend component Type Family is the same as fi.Id
                if ff.Id == fi.Family.Id:
                    instances.add(e)
            except:
                pass
                # print(fs.Id.IntegerValue)
    return instances
# def purge_families_recurs(doc):
#     doc_families = get_families(doc)
#     # trans_man = TransactionManager.Instance
#     for df in doc_families:
#         if df.IsInPlace:
#             continue
#         famdoc = doc.EditFamily(df)
#         # if df.Id != ElementId(764909):
#         #     continue
#
#         if famdoc == None or not famdoc.IsFamilyDocument:
#             print("Family %s is invalid" % famdoc.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString())
#             continue
#         print(df.Name)
#         print(purge(famdoc))
#         fam_loaded = famdoc.LoadFamily.Overloads.Functions[3](doc, FamilyLoadOption())
#         famdoc.Close(False)
#
#         # print('fam_loaded',df.Id,fam_loaded.Id)
#         # break
#         # for f in get_families:
#         #     print(f)


PURGE_RESULTS = {}
PURGE_SIZES_SUM = 0


def filter_elements_by_depenencies(doc, els, deps):
    in_use = []
    not_in_use = []
    # print(els)
    for e in els:
        if e.Id.IntegerValue in deps:
            in_use.append(e)
        else:
            not_in_use.append(e)
    return in_use, not_in_use


def len_of_two(a, b):
    print("len_of_two %d, %d" % (len(a), len(b)))


def file_size(f):
    if not os.path.exists(f):
        return 0
    file_size = os.stat(f).st_size
    # print(file_size)
    file_size = float(file_size) / (1024 * 1024)
    # print(file_size)
    return file_size


def save_family(doc, directory, after=False):
    fam_save_options = SaveAsOptions(OverwriteExistingFile=True, MaximumBackups=1)
    fam_file = doc.Title
    if after:
        directory = os.path.join(directory, "_AFTER")
    if not os.path.exists(directory):
        os.makedirs(directory)
        # _fam_file,_fam_file_ext = os.path.split(fam_file)
        # fam_file = _fam_file + "_AFTER.rfa"

    fam_save_path = os.path.join(directory, fam_file)
    try:
        doc.SaveAs(fam_save_path, fam_save_options)
    except Exception as e:
        print(e)
        print(fam_save_path)
    return fam_save_path, fam_file


def process_purge(doc, purgers, parent=None, level=0, max_level=1, directory=None, skipped_title=None):
    global PURGE_RESULTS
    global PURGE_SIZES_SUM
    global PURGE_RESULTS_CSV
    global START_TIME

    families_in_use, families_not_in_use = get_families(doc)
    purge_result_purged = 0
    purge_result_found = 0
    purge_result_by_func = {}

    title_printed = False
    tbs = "\t" * level

    if not skipped_title:
        skipped_title = ""

    skipped_title += "\n" + tbs + doc.Title

    if parent == None:
        print(skipped_title)
        title_printed = True
        START_TIME = time.time()

    if level > 0:
        dependencies = dependencies_structure(doc)
        in_use, not_in_use = filter_elements_by_depenencies(doc, families_not_in_use, dependencies)

        families_not_in_use = list(set(families_not_in_use) - set(in_use))
        families_in_use = list(set(families_in_use + in_use))
        # print(len_of_two(families_in_use, families_not_in_use))


        t = Transaction(doc, "Purge")
        t.Start()

        for purge_func in purgers:
            prg_name = purge_func.__name__
            prg_result = None
            purge_result_by_func[prg_name] = 0

            if prg_name == "Families":
                if len(families_not_in_use) == 0:
                    continue
                if len(families_not_in_use) > 0:
                    prg_result = purge_func(doc, dependencies, fam_not_used=families_not_in_use)

            else:
                prg_result = purge_func(doc, dependencies)

            if prg_result == None:
                print(prg_name, "None")
                prg_result = (0, 0, [])
            prg_count, prg_count_found, prg_failed = prg_result

            if prg_name == "Families":
                families_in_use += prg_failed

            purge_result_purged += prg_count
            purge_result_found += prg_count_found

            if prg_count_found > 0 or prg_count > 0:

                if prg_name not in PURGE_RESULTS.keys():
                    PURGE_RESULTS[prg_name] = 0

                PURGE_RESULTS[prg_name] += prg_count
                purge_result_by_func[prg_name] = prg_count

                if not title_printed:
                    print(skipped_title)
                    title_printed = True

                if prg_count != prg_count_found:
                    print(tbs + "\t%s -%d of %d" % (prg_name, prg_count, prg_count_found,))
                else:
                    print(tbs + "\t%s -%d" % (prg_name, prg_count))

        t.Commit()

    # print("families_used", len(families_in_use))
    families_in_use = list(set(families_in_use))
    families_in_use_len = len(families_in_use)

    # print("families_not_used_filtered", len(families_not_used_filtered))
    if level == 0:
        families_not_in_use = list(set(families_not_in_use))
        families_not_in_use_len = len(families_not_in_use)
        families_in_use += families_not_in_use
        families_in_use_len = len(families_in_use)
        # if PURGE_NOTUSED_FAMILIES:
        #     # t = Transaction(doc, "Purge")
        #     # t.Start()  
        #     # for f in families_not_in_use:
        #     #     try:
        #     #         print("Delete %s" % f.Name)
        #     #         doc.Delete(f.Id)
        #     #     except:
        #     #         print("Error with deleting %s" % f.Name)
        #     # t.Commit()
        _csv = []
        for fi in range(len(families_in_use)):
            _line = [fi,families_in_use[fi].Name]
            _csv.append(_line)
        write_csv(os.path.join(directory, doc.Title + "_list"), _csv)
        print("Families found: %d\n(%d in use, %d not in use)" % (
            len(families_in_use), families_in_use_len, families_not_in_use_len))
        print("Search took %s seconds\n\nPurge process started" % (time_elapsed()))

        START_TIME = time.time()
    # families_in_use_len = len(families_in_use)

    # open and purge each of selected get_families
    if level < max_level or max_level == None:
        if title_printed:
            skipped_title = None

        for fi in range(len(families_in_use)):
            _purge_result_by_func = {}
            f = families_in_use[fi]

            if f == None or f.IsInPlace or not f.IsEditable:
                continue

            if f.Name == os.path.splitext(doc.Title)[0]:
                t = Transaction(doc, "Purge")
                t.Start()
                try:

                    f.Name = f.Name + "_"
                    t.Commit()
                    print(f.Name + " renamed")
                except Exception as e:
                    t.Rollback()
                    print("rename error", e)
                    continue
            # update stats - progress bar and window title
            if parent == None:
                percent_done = float(fi) / families_in_use_len
                output.update_progress(int(100 * percent_done), 100)
                if percent_done > 0.01:
                    time_left = time_elapsed() * ((1 / percent_done) - 1)
                    time_left_text = " - %s left - %.3f Mb purged" % (time_format(time_left), PURGE_SIZES_SUM)
                else:
                    time_left_text = ""
                output.set_title("%s - %d of %d finished%s" % (
                    window_title, fi, families_in_use_len, time_left_text))

            fam_doc = doc.EditFamily(f)

            if directory:
                try:
                    fam_save_path, fam_file = save_family(fam_doc, directory)
                except Exception as e:
                    print("Unable to save", e)
                    fam_doc.Close(False)
                    break
                _directory = os.path.join(directory, fam_file[:-4][:32].strip())
            else:
                _directory = None

            if fam_doc == None or not fam_doc.IsFamilyDocument:
                print(tbs + "Family %s is invalid" % fam_doc.get_Parameter(
                    BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString())
                continue

            fam_doc, _purge_result_purged, __purge_result_by_func = process_purge(fam_doc, purgers, parent=doc,
                                                                                  level=level + 1, max_level=max_level,
                                                                                  directory=_directory,
                                                                                  skipped_title=skipped_title)
            for pk in __purge_result_by_func:
                if pk not in _purge_result_by_func.keys():
                    _purge_result_by_func[pk] = 0
                _purge_result_by_func[pk] += __purge_result_by_func[pk]

            if os.path.exists(_directory):
                if not os.listdir(_directory):
                    os.rmdir(_directory)

            purge_result_purged += _purge_result_purged

            fam_size_before = 0
            fam_size_after = 0
            fam_size_diff = 0

            if directory and os.path.exists(fam_save_path):
                fam_size_before = file_size(fam_save_path)

                if _purge_result_purged > 0:
                    _fam_save_path, _fam_file = save_family(fam_doc, directory, after=True)

                    fam_size_after = file_size(_fam_save_path)
                    fam_size_diff = (fam_size_after - fam_size_before)

                    if fam_size_diff != 0:
                        print(tbs + "\t%.3f Mb (%.3f -> %.3f, %d%%)" % (
                            fam_size_diff, fam_size_before, fam_size_after,
                            -(1 - fam_size_after / fam_size_before) * 100))
                        if parent == None:
                            PURGE_SIZES_SUM += fam_size_diff

                else:
                    tries = 4
                    while tries > 0:
                        try:
                            os.remove(fam_save_path)
                            tries = 0
                        except Exception as e:
                            print(e)
                            print(fam_save_path)
                            tries -= 1
                            if tries > 0:
                                time.sleep(0.5)
                                print("Trying again")

            # writing to CSV
            try:
                fam_type = str(fam_doc.OwnerFamily.FamilyCategory.Name)
            except:
                fam_type = "Not family"
            csv_line = [str(level), fam_type, fam_doc.Title, locale.str(fam_size_before),
                        locale.str(fam_size_after),
                        locale.str(fam_size_diff)]
            for pk in _purge_result_by_func:
                csv_line.append(str(_purge_result_by_func[pk]))
            PURGE_RESULTS_CSV.append(csv_line)

            # Load family to parent document
            if fam_size_diff < 0:
                fam_doc.LoadFamily.Overloads.Functions[3](doc, FamilyLoadOption())
            fam_doc.Close(False)

    return doc, purge_result_purged, purge_result_by_func


class CheckBoxFunc:
    def __init__(self, func, default_state=False):
        self.func = func
        self.name = func.__name__
        if self.name[-4:] == "_wip":
            self.state = False
            self.name = self.name[:-4]
        else:
            self.state = default_state

    def __nonzero__(self):
        return self.state

    def __bool__(self):
        return self.state


def create_directory(file, top_dir=PURGE_DIR, date=True):
    # print(file)
    if date:
        time_stamp = "_" + datetime.now().strftime("%y%m%d_%H-%M-%S")
    else:
        time_stamp = ""
    file = file.replace(".", "_") + time_stamp
    full_path = os.path.join(top_dir, file)
    if not os.path.exists(full_path):
        os.makedirs(full_path)

    return full_path

def time_elapsed():
    global START_TIME
    return time.time() - START_TIME

def roundup(x):
    return int(math.ceil(x / 10.0)) * 10

def time_format(t):
    if t < 60:
        return "%d sec" % t
    elif t < 120:
        s = t % 60
        m = t / 60
        return "%d m %d sec" % (m, roundup(s))
    elif t < 6000:
        return "%d min" % (float(t) / 60)
    else:
        _m = float(t) / 60
        m = _m % 60
        h = t / 3600
        return "%d h %d min" % (h, roundup(m))


def main():
    global PURGE_RESULTS_CSV
    global START_TIME
    global PURGE_NOTUSED_FAMILIES

    # q = TaskDialog.Show(__title__, "Purge not used families?",
    #                             TaskDialogCommonButtons.Ok | TaskDialogCommonButtons.Cancel)
    # if str(q) == "Ok":
    #     PURGE_NOTUSED_FAMILIES = True

    purgers = Purgers()
    directory = create_directory(doc.Title)
    options = []
    selected_purgers = []

    for f in dir(purgers):
        func = purgers.__getattribute__(f)
        if type(func) == types.MethodType and f[0] != "_":

            opt = CheckBoxFunc(func, True)
            options.append(opt)
    if len(options) > 1:
        all_checkboxes = SelectFromCheckBoxes.show(options,title='Select cleaners to Purge', width=300, button_name='Purge!')
        if all_checkboxes:
            selected_purgers = [c.func for c in all_checkboxes if c.state == True]
    else:
        selected_purgers = [c.func for c in options]

    if len(selected_purgers) > 0:
        PURGED_COUNT = 0
        level = 0
        max_level = 99
        if doc.Title[-4:] == ".rfa":
            level = 1

        if __shiftclick__:
            max_level = 1

        START_TIME = time.time()
        print(directory)

        csv_line = ["Level", "Category", "Family name", "Size before", "Size after", "Size diff"]

        for pk in selected_purgers:
            csv_line.append("Purged: " + str(pk.__name__))

        PURGE_RESULTS_CSV.append(csv_line)

        process_purge(doc, selected_purgers, level=level, max_level=max_level, directory=directory)
        output.set_title("%s - Write CSV" % (window_title,))
        write_csv(directory)
        output.set_title("%s - Done" % (window_title,))

        print("\n\nFinished")
        for r in PURGE_RESULTS.keys():
            c = PURGE_RESULTS[r]
            print("%s: %d" % (r, c))
            PURGED_COUNT += c
        print('\nTOTAL purged: %d' % PURGED_COUNT)
        print('SIZE DIFFERENCE: %.3f Mb' % PURGE_SIZES_SUM)

        print("\n\n--- %s ---" % (time_format(time_elapsed())))

        output.update_progress(100, 100)

    else:
        print("nothing selected")

if __name__ == '__main__':
    main()
