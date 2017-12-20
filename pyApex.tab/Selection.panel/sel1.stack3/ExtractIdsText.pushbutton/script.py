# -*- coding: utf-8 -*-
__title__ = 'Extract IDs from text'
__doc__ = """Extracts all elements Ids from pasted text. Useful to select elements from Warnings - just copy text from HTML report.
Also works with one id per line inputs, e.g. with text copied from spreadsheets.

Извлекает ID элементов из вставленного текста. Полезно для выбора элементов из отчетов о предупреждениях - просто скопируйте текст из HTML-отчета.
Также работает с текстом, в котором каждая строка - отдельный ID, например скопированным из таблицы."""

__helpurl__ = "https://apex-project.github.io/pyApex/help#extract-ids-from-text"

try:
    from pyrevit.versionmgr import PYREVIT_VERSION
except:
    from pyrevit import versionmgr
    PYREVIT_VERSION = versionmgr.get_pyrevit_version()

pyRevitNewer44 = PYREVIT_VERSION.major >=4 and PYREVIT_VERSION.minor >=5

if pyRevitNewer44:
    from pyrevit import script, revit
    output = script.get_output()
    logger = script.get_logger()
    linkify = output.linkify
    doc = revit.doc
    uidoc = revit.uidoc
    selection = revit.get_selection()
    datafile = script.get_document_data_file("SelList", "pym")
else:
    from scriptutils import logger, this_script
    from revitutils import doc, uidoc

    output = this_script.output
    datafile = this_script.get_document_data_file(0, "pym", command_name="SelList")

import os
import re
import pickle as pl
import clr

from System.Collections.Generic import List
from Autodesk.Revit.DB import ElementId



def addtoclipboard(text):
    logger.debug('Copying IDs to clipboard')
    command = 'echo ' + text.strip() + '| clip'
    os.system(command)
    logger.debug('Copying IDs to clipboard - OK')


def strip(value):
    if value:
        v = value.strip("\n").strip(" ").strip("\t").strip("\r")
        if len(v) == 0:
            return
        else:
            return v
    else:
        return


def parse(value, reduce_duplicates = False):
    value = strip(value)

    if not value:
        logger.error("Text is empty")
        return

    value_lines = value.split("\n")

    errors = []

    ids_str = []
    ids_element_ids = []

    for v in range(len(value_lines)):
        vl = value_lines[v]
        vl = strip(vl)

        if not vl:
            continue

        _id = None

        try:
            _id = int(vl)
        except:
            pass

        if not _id:
            m = re.search(r"(id|Код)\s+([0-9]{1,})[^0-9]*", vl)
            try:
                _id = int(str(m.group(2)))
            except:
                pass

        if _id:
            e_id = ElementId(_id)
            ids_element_ids.append(e_id)
            ids_str.append(str(_id))
        else:
            errors.append("%d: %s" % (v, vl))

    if len(ids_element_ids) > 0:
        print('%d elements selected:' % len(ids_element_ids))
        elements_strs = []

        if reduce_duplicates:
            ids_element_ids = set(ids_element_ids)
            ids_str = set(ids_str)

        for idx, elid in enumerate(ids_element_ids):
            elements_strs.append(output.linkify(elid))
        print(",".join(elements_strs))

        # # Copy ids to clipboard
        # addtoclipboard(",".join(set(ids_str)))

        # Select objects
        ids_element_ids_list = List[ElementId](ids_element_ids)
        selection = uidoc.Selection
        selection.SetElementIds(ids_element_ids_list)

        # Save selection
        try:
            f = open(datafile, 'w')
            pl.dump(ids_str, f)
            f.close()
        except Exception as io_err:
            logger.error('Error read/write to: {} | {}'.format(datafile, io_err))

    else:
        print("No IDs were found")

    if len(errors) > 0:
        logger.error("Ids weren't found on lines: \n" + "\n".join(errors))


from scriptutils import this_script
from scriptutils.userinput import WPFWindow

my_config = this_script.config

class ExtractIdsTextWindow(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)

        self.text.Text = "Paste text from warnings report or any text you want to extract IDs from"

        try:
            self.reduce_duplicates.IsChecked = my_config.reduce_duplicates
        except:
            self.reduce_duplicates.IsChecked = my_config.reduce_duplicates = False

    # noinspection PyUnusedLocal
    # noinspection PyMethodMayBeStatic
    def send(self, sender, args):
        my_config.reduce_duplicates = self.reduce_duplicates.IsChecked
        this_script.save_config()
        parse(self.text.Text, reduce_duplicates = self.reduce_duplicates.IsChecked)
        self.Close()


if __name__ == '__main__':
    ExtractIdsTextWindow('window.xaml').ShowDialog()
    output.set_width(400)
    output.set_height(400)
