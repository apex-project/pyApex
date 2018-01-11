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

    my_config = script.get_config()
else:
    from scriptutils import this_script as script
    from scriptutils.userinput import WPFWindow, pick_folder
    my_config = script.config

    from Autodesk.Revit.UI import TaskDialog
    def alert(msg):
        TaskDialog.Show('pyrevit', msg)

import show_dependent_defaults as cdef
import pyapex_utils as pau

class ShowDependentConfigWindow(WPFWindow):
    def __init__(self, xaml_file_name):

        WPFWindow.__init__(self, xaml_file_name)
        try:
            self.limit.Text = str(my_config.limit)
        except:
            self.restore_defaults(None,None,"limit")

        try:
            self.exceptions.Text = pau.list2str(my_config.exceptions)
        except:
            self.restore_defaults(None,None,"exceptions")


    def restore_defaults(self, p1=None, p2=None, *args):
        if len(args) == 0 or "limit" in args:
            self.limit.Text = str(cdef.limit)

        if len(args) == 0 or "exceptions" in args:
            self.exceptions.Text = pau.list2str(cdef.exceptions)

    # noinspection PyUnusedLocal
    # noinspection PyMethodMayBeStatic
    def save_options(self, sender, args):
        errors = []
        try:
            my_config.exceptions = pau.str2list(self.exceptions.Text)
        except:
            errors.append("Exceptions value is invalid")

        try:
            v = int(self.limit.Text)
            assert v >= 0
            my_config.limit = v
        except:
            errors.append("Limit value should be either zero or a positive integer")

        if errors:
            alert("Can't save config.\n" + "\n".join(errors))
            return
        else:
            script.save_config()
            self.Close()

    def NumberValidationTextBox(self, sender, e):
        try:
            x = int(e.Text.strip())
            e.Handled = False
        except:
            e.Handled = True


if __name__ == '__main__':
    ShowDependentConfigWindow('ShowDependentConfig.xaml').ShowDialog()
