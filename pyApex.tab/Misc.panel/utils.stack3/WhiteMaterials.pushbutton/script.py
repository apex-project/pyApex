# -*- coding: utf-8 -*- 
__doc__ = """Changes appearance of all project materials to 'white' and back. Useful for paper-like render.
You can set default material (White) and exceptions (Glass, Wood etc.) in command config (run with Shift-click)

Изменяет отображение всех материалов в проекте на 'белый'. Удобно для создание 'бумажных' визуализаций.
Для выбора имени материла по-умолчанию и настроек исключений (например, стекло или дерево), запустите с зажатым Shift
"""

__title__ = 'White Materials'
__helpurl__ = "https://apex-project.github.io/pyApex/help#white-materials"

try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr
    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >=4 and PYREVIT_VERSION.minor >=5

if pyRevitNewer44:
    from pyrevit import script, revit
    from pyrevit.revit import uidoc, doc
    from pyrevit.forms import CommandSwitchWindow
    output = script.get_output()
    logger = script.get_logger()
    linkify = output.linkify
    selection = revit.get_selection()
    my_config = script.get_config()

else:
    from scriptutils import logger, this_script as script
    from revitutils import doc,  uidoc
    from scriptutils.userinput import CommandSwitchWindow
    output = script.output
    my_config = script.config

import os
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import *
from datetime import datetime
import re
import pickle as pl


def config_ignore_transparent():
    try:
        v = my_config.ignore_transparent
    except:
        import white_materials_defaults as cdef
        v = cdef.ignore_transparent
    return v


def config_material():
    try:
        v = my_config.material
    except:
        import white_materials_defaults as cdef
        v = cdef.material
    return v


def config_exceptions():
    try:
        v = my_config.exceptions
    except:
        import white_materials_defaults as cdef
        v = cdef.exceptions
        my_config.exceptions = v
    return v


def backup_datafile(f):
    try:
        _new_path, ext = os.path.splitext(f)
        new_path = _new_path + datetime.now().strftime("_%y%m%d_%H-%M-%S") + ext
        os.rename(f, new_path)
        logger.debug("Datafile backed up to %s" % new_path)
    except Exception as e:
        logger.error("Error renaming datafile\n" + str(e))


def change_materials(reverse=False, datafile=None, limit=None):
    mat_dict = {}

    white_material_name = config_material()
    materials_exceptions = config_exceptions()
    ignore_transparent = config_ignore_transparent()

    if os.path.exists(datafile):
        logger.debug("Datafile found %s" % datafile)
        if reverse == False:
            logger.debug("New materials will be added")
        f = open(datafile, 'r')
        mat_dict = pl.load(f)
        f.close()
    else:
        logger.debug("New datafile %s" % datafile)

    cl = FilteredElementCollector(doc)
    mats = list(cl.OfCategory(BuiltInCategory.OST_Materials).WhereElementIsNotElementType().ToElements())

    try:
        white_mat = filter(lambda x: x.Name == white_material_name, mats)[0]
    except Exception as e:
        logger.error("Material '%s' not found" % white_material_name)
        logger.error(e)
        return

    white_mat_a = white_mat.AppearanceAssetId

    logger.info("White material: %s\nAssetId: %d" % (white_material_name, white_mat_a.IntegerValue))

    t = Transaction(doc)
    t.Start(__title__ + (" reverse" if reverse else ""))

    if limit>0:
        mats = mats[:limit]
    for m in mats:
        m_name = m.Name
        m_name_ignore = False
        for r in materials_exceptions:
            re_match = re.match(r, m_name, re.I)
            if re_match:
                m_name_ignore = True
                break

        if m_name_ignore:
            logger.info("%s - ignore name" % m_name)
            continue

        if m.Transparency != 0 and ignore_transparent:
            logger.info("%s - ignore transparency" % m_name)
            continue

        m_id = m.Id.IntegerValue
        a_id = m.AppearanceAssetId.IntegerValue

        if reverse == False:
            if a_id != white_mat_a.IntegerValue:
                mat_dict[m_id] = a_id
                m.AppearanceAssetId = white_mat_a
                logger.info("%s (%d, asset %d) changed to white" % (m_name, m_id, a_id))
            else:
                logger.info("%s (%d) wasn't change" % (m_name, m_id))
        else:
            try:
                _id = mat_dict[m_id]
                m.AppearanceAssetId = ElementId(_id)

                logger.info("%s (%d) changed to %d" % (m_name, m_id, _id))
            except:
                logger.info("%s (%d) not found or wasn't change" % (m_name, m_id))

    t.Commit()
    if reverse == False:
        f = open(datafile, 'w')
        pl.dump(mat_dict, f)
        f.close()
    else:
        backup_datafile(datafile)
    print("Completed")


def main():
    if __forceddebugmode__:
        limit = 10
        logger.debug("limit %d" % limit)
    else:
        limit = None

    reverse = False

    x,file_name = os.path.split(doc.PathName)
    file_id, x = os.path.splitext(file_name)
    if len(file_id) == 0:
        file_id = doc.Title
    datafile = script.get_data_file(file_id, "pym")

    if os.path.exists(datafile):
        options = ["Make White", "Revert original"]
        if pyRevitNewer44:
            selected_switch = CommandSwitchWindow.show(options,
                                               message='Select direction')
        else:
            selected_switch = CommandSwitchWindow(options,
                                                       message='Select direction').pick_cmd_switch()

        if selected_switch == "Revert original":
            reverse = True

    change_materials(reverse, datafile=datafile, limit=limit)

if __name__ == '__main__':
    main()
