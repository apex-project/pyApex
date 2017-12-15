from scriptutils import this_script
from scriptutils.userinput import WPFWindow


my_config = this_script.config


class LevelDependenceConfigWindow(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)

        try:
            self.exceptions.Text = str(my_config.exceptions)
            self.limit.Text = str(my_config.limit)
        except:
            self.exceptions.Text = my_config.exceptions = ""
            self.limit.Text = my_config.limit = "50"

            this_script.save_config()

    # noinspection PyUnusedLocal
    # noinspection PyMethodMayBeStatic
    def save_options(self, sender, args):
        my_config.exceptions = self.exceptions.Text
        my_config.limit = self.limit.Text

        this_script.save_config()
        self.Close()


    def NumberValidationTextBox(self, sender, e):
        try:
            x = int(e.Text.strip())
            e.Handled = False
        except:
            e.Handled = True

if __name__ == '__main__':
    LevelDependenceConfigWindow('LevelDependenceConfig.xaml').ShowDialog()
