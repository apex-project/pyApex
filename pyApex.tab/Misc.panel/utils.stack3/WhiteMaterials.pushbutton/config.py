# -*- coding: utf-8 -*-
try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr

    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >= 4 and PYREVIT_VERSION.minor >= 5

if pyRevitNewer44:
    from pyrevit import script
    from pyrevit.forms import WPFWindow, alert
    logger = script.get_logger()
    my_config = script.get_config()
else:
    from scriptutils import this_script as script
    from scriptutils import logger
    from scriptutils.userinput import WPFWindow, pick_folder
    my_config = script.config

    from Autodesk.Revit.UI import TaskDialog
    def alert(msg):
        TaskDialog.Show('pyrevit', msg)

import white_materials_defaults as cdef
import pyapex_utils as pau

class WhiteMaterialsConfigWindow(WPFWindow):
    def __init__(self, xaml_file_name):

        WPFWindow.__init__(self, xaml_file_name)
        try:
            self.exceptions.Text = pau.list2str(my_config.exceptions)
        except:
            self.restore_defaults(None,None,"exceptions")

        try:
            self.material.Text = pau.list2str(my_config.material)
        except:
            self.restore_defaults(None,None,"material")

        try:
            self.ignore_transparent.IsChecked = bool(my_config.ignore_transparent)
        except:
            self.restore_defaults(None,None,"ignore_transparent")

    def restore_defaults(self, p1=None, p2=None, *args):
        if len(args) == 0 or "exceptions" in args:
            self.exceptions.Text = pau.list2str(cdef.exceptions)
        if len(args) == 0 or "material" in args:
            self.material.Text = pau.list2str(cdef.material)
        if len(args) == 0 or "ignore_transparent" in args:
            self.ignore_transparent.IsChecked = bool(cdef.ignore_transparent)

    # noinspection PyUnusedLocal
    # noinspection PyMethodMayBeStatic
    def save_options(self, sender, args):
        errors = []
        try:
            my_config.exceptions = pau.str2list(self.exceptions.Text.encode('utf-8'))
        except:
            errors.append("Exceptions value is invalid")

        try:
            v = self.material.Text
            assert len(v) >= 0

            my_config.material = v.encode('utf-8')
        except Exception as exc:
            errors.append("Material name is invalid")
            logger.debug(exc)

        try:
            my_config.ignore_transparent = bool(self.ignore_transparent.IsChecked)
        except:
            errors.append("Ignore transparent value is invalid")

        if errors:
            alert("Can't save config.\n" + "\n".join(errors))
            return
        else:
            script.save_config()
            self.Close()


if __name__ == '__main__':
    WhiteMaterialsConfigWindow('WhiteMaterialsConfig.xaml').ShowDialog()
