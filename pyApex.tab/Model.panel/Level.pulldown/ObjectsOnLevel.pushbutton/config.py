try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr

    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >= 4 and PYREVIT_VERSION.minor >= 5

if pyRevitNewer44:
    from pyrevit import script
    from pyrevit.forms import WPFWindow

    my_config = script.get_config()
else:
    from scriptutils import this_script as script
    from scriptutils.userinput import WPFWindow
    my_config = script.config

class LevelDependenceConfigWindow(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)

        try:
            self.limit.Text = str(my_config.limit)
        except:
            self.limit.Text = my_config.limit = "50"

        try:
            self.exceptions.Text = str(my_config.exceptions)
        except:

            script.save_config()

    # noinspection PyUnusedLocal
    # noinspection PyMethodMayBeStatic
    def save_options(self, sender, args):
        my_config.exceptions = self.exceptions.Text
        my_config.limit = self.limit.Text

        script.save_config()
        self.Close()


    def NumberValidationTextBox(self, sender, e):
        try:
            x = int(e.Text.strip())
            e.Handled = False
        except:
            e.Handled = True

if __name__ == '__main__':
    LevelDependenceConfigWindow('LevelDependenceConfig.xaml').ShowDialog()
