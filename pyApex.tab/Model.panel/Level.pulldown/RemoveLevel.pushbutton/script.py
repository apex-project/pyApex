# -*- coding: utf-8 -*-
__title__ = 'Remove Level Safely'
__doc__ = """Move all elements based on specified level onto another level"""

__helpurl__ = "https://apex-project.github.io/pyApex/help#remove-level"
__beta__ = True

try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr
    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >=4 and PYREVIT_VERSION.minor >=5

if pyRevitNewer44:
    from pyrevit import script, revit
    from pyrevit.forms import SelectFromList, SelectFromCheckBoxes
    output = script.get_output()
    logger = script.get_logger()
    linkify = output.linkify
    doc = revit.doc

else:
    from scriptutils import logger
    from scriptutils.userinput import SelectFromList, SelectFromCheckBoxes
    from revitutils import doc

from Autodesk.Revit.DB import *

class CheckBoxLevel:
    def __init__(self, level, default_state=False):
        self.level = level
        self.name = level.Name
        self.state = default_state

    def __str__(self):
        return self.name

    def __nonzero__(self):
        return self.state

    def __bool__(self):
        return self.state


def LevelChangePreselected(selected_ids, target_level_id):
    errors = []
    changed = []
    t = Transaction(doc, 'Change level to 0')
    t.Start()
    for e_id in selected_ids:
        el = doc.GetElement(e_id)
        try:
            levelID = el.LevelId  # Initial level of object, assigned on element creation
            if levelID.IntegerValue < 0:
                continue

            LevelToElement = doc.GetElement(levelID)

            LevElev = LevelToElement.get_Parameter(BuiltInParameter.LEVEL_ELEV).AsValueString().replace(" ", "")

            offset = el.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)

            if not offset:
                offset = el.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM)

            if not offset:
                offset = el.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET)

            if not offset:
                offset = el.get_Parameter(BuiltInParameter.ROOM_LOWER_OFFSET)
                
            print(offset.AsValueString())
            finalElev = float(LevElev) + float(offset.AsValueString().replace(" ", ""))
            print(offset.AsValueString(), finalElev)
            offset.SetValueString(str(finalElev))

            baselevel = el.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)
            if not baselevel:
                baselevel = el.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)
                # if baselevel:
                #     baseoffset = el.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET)
                #     finalOffset = float(LevElev) + float(offset.AsValueString().replace(" ", ""))
            baselevel.Set(target_level_id)

            changed.append(str(e_id.IntegerValue))
        except Exception as e:
            try:
                print("%s %s - %s" % (str(e_id.IntegerValue),str(el.GetType()),str(e)))
            except:
                print("%s - %s" % (str(e_id.IntegerValue), str(e)))
            errors.append(str(e_id.IntegerValue))
    t.Commit()

    return errors, changed

def main():
    cl = FilteredElementCollector(doc)
    levels_all = cl.OfCategory(BuiltInCategory.OST_Levels).WhereElementIsNotElementType().ToElements()

    options = []
    for l in levels_all:
        cb = CheckBoxLevel(l)
        options.append(cb)

    if len(options) == 0:
        print("Levels wasn't found")
        return

    selected1 = SelectFromCheckBoxes.show(options, title='Select levels to delete', width=300,
                                               button_name='OK')
    selected_levels1 = [c.level for c in selected1 if c.state == True]

    if not selected_levels1:
        print("Nothing selected")
        return

    options = [c for c in selected1 if c.state != True]

    if len(options) == 0:
        print("You selected all levels")
        return

    selected2 = SelectFromList.show(options, title='Select target level', width=300,
                                          button_name='OK')
    if not selected2:
        print("Nothing selected")
        return

    selected_levels2 = [c.level for c in selected2]
    target_level = selected_levels2[0]
    errors = set()
    changed = set()
    for l in selected_levels1:
        objects_to_change = []

        t = Transaction(doc, "Check level " + l.Name)
        t.Start()
        elements = doc.Delete(l.Id)
        t.RollBack()

        errors_, changed_ = LevelChangePreselected(elements, target_level.Id)

        errors = errors.union(set(errors_))
        changed = changed.union(set(changed_))

    if errors:
        logger.error("Errors")
        logger.error( ",".join(list(errors)))

    if changed:
        print("\nChanged succesfully")
        print( ",".join(list(changed)))
    else:
        logger.error("No object were changed")


main()
