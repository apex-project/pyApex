# -*- coding: utf-8 -*-
__title__ = 'Level dependencies'
__doc__ = 'List elements dependent of selected level\nYou can select plan view to check its level'

__helpurl__ = "https://apex-project.github.io/pyApex/help#level-dependencies"

from Autodesk.Revit.DB import *
from pyrevit.forms import SelectFromList, SelectFromCheckBoxes
from pyrevit import script, revit
from pyrevit.revit import doc, uidoc

output = script.get_output()
logger = script.get_logger()
selection = revit.get_selection()


ignore_types = [Level,SunAndShadowSettings,Viewport,SketchPlane, Sketch]

if len(selection) == 0:
    logger.error('Please, select level or plan view')
else:
    
    for s_id in selection.element_ids:
        e = doc.GetElement(s_id)
        if type(e) == ViewPlan:
            e = e.GenLevel
        elif type(e) == Level:
            pass
        else:
            continue
        t = Transaction(doc, "Check level " + e.Name)
        t.Start()
        try:
            elements = doc.Delete(s_id)
        except:
            pass
        t.RollBack()
        element_ids = []

        i = 0

        elements_count = len(elements)
        print('{}'.format(output.linkify(selection.element_ids,
                                             title='%d elements on level %s' % (elements_count, e.Name ))))
        for edid in elements:
            ed = doc.GetElement(edid)
            if not ed:
                continue
            if type(ed) in ignore_types:
                continue
            element_ids.append(str(edid.IntegerValue))
            print('{}: {} {}'.format(i, output.linkify(edid), ed.GetType().ToString()))
            i+=1

            if i >= 50:
                print("+ %d" % (elements_count - i))
                break

        print("\n\t"  + ",".join(element_ids))
        print("\n\n")

