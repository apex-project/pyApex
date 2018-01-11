# -*- coding: utf-8 -*-
try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr

    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >= 4 and PYREVIT_VERSION.minor >= 5

if pyRevitNewer44:
    from pyrevit import script
    from pyrevit.forms import WPFWindow, alert, pick_folder

    my_config = script.get_config()
else:
    from scriptutils import this_script as script
    from scriptutils.userinput import WPFWindow, alert, pick_folder
    my_config = script.config

import purge_families_defaults as cdef
import pyapex_utils as pau
import os

class PurgeFamiliesConfigWindow(WPFWindow):
    def __init__(self, xaml_file_name):

        WPFWindow.__init__(self, xaml_file_name)
        try:
            self.temp_dir.Text = pau.list2str(my_config.temp_dir)
        except:
            self.restore_defaults(None,None,"temp_dir")

    def restore_defaults(self, p1=None, p2=None, *args):
        if len(args) == 0 or "temp_dir" in args:
            self.temp_dir.Text = pau.list2str(cdef.temp_dir)

    # noinspection PyUnusedLocal
    # noinspection PyMethodMayBeStatic
    def save_options(self, sender, args):
        errors = []
        directory = self.temp_dir.Text
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)

            if not os.path.isdir(directory):
                errors.append("Specified path is not a directory")
        except Exception as e:
            errors.append("Specified path is invalid. Unknown error\n%s" % str(e))

        if errors:
            alert("Can't save config.\n" + "\n".join(errors))
            return
        else:
            script.save_config()
            self.Close()

    def pick(self, sender, args):
        path = pick_folder()
        if path:
            self.temp_dir.Text = path


if __name__ == '__main__':
    PurgeFamiliesConfigWindow('PurgeFamiliesConfig.xaml').ShowDialog()
