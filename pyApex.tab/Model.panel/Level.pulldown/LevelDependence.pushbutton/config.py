# -*- coding: utf-8 -*-
try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr
    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >=4 and PYREVIT_VERSION.minor >=5

# if pyRevitNewer44:
#     from pyrevit import script, revit
#     output = script.get_output()
#     logger = script.get_logger()
#     linkify = output.linkify
#     selection = revit.get_selection()
#     uidoc = revit.uidoc
#     doc = revit.doc
# else:
#     from scriptutils import logger, this_script
#     from revitutils import doc, selection, uidoc
#     output = this_script.output


print("Config")