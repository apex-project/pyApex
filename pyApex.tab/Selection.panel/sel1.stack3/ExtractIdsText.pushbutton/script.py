# -*- coding: utf-8 -*-
__title__ = 'Extract IDs from text'
__doc__ = """Extracts all elements Ids from pasted text. Useful to select elements from Warnings - just copy text from HTML report.
Also works with one id per line inputs, e.g. with text copied from spreadsheets.

Извлекает ID элементов из вставленного текста. Полезно для выбора элементов из отчетов о предупреждениях - просто скопируйте текст из HTML-отчета.
Также работает с текстом, в котором каждая строка - отдельный ID, например скопированным из таблицы."""

__helpurl__ = "https://apex-project.github.io/pyApex/help#extract-ids-from-text"

import os
import re
import pickle as pl
import clr

clr.AddReferenceByPartialName('System.Windows.Forms')
clr.AddReferenceByPartialName('System.Drawing')
from Autodesk.Revit.DB import ElementId
from System.Windows.Forms import Application, Button, Form, Label, CheckBox, DialogResult, TextBox, RadioButton, \
    FormBorderStyle
from System.Drawing import Point, Icon, Size
from pyrevit import script, revit

output = script.get_output()
logger = script.get_logger()
selection = revit.get_selection()

linkify = output.linkify

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

datafile = script.get_document_data_file("SelList", "pym")


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


def parse(value):
    value = strip(value)

    if not value:
        logger.error("Text is empty")
        return

    value_lines = value.split("\n")

    errors = []
    ids_str = set()
    ids_element_ids = set()

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
            ids_element_ids.add(e_id)
            ids_str.add(str(_id))
        else:
            errors.append("%d: %s" % (v, vl))

    if len(ids_element_ids) > 0:
        logger.info('%d elements selected and copied to clipboard:')

        elements_strs = []
        for idx, elid in enumerate(ids_element_ids):
            elements_strs.append(output.linkify(elid))
        print(",".join(elements_strs))

        # Copy ids to clipboard
        addtoclipboard(",".join(set(ids_str)))

        # Select objects
        selection = uidoc.Selection
        selection.SetElementIds(ids_element_ids)

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



class pyRevitPlusForm(Form):
    global parse

    def __init__(self):
        self.Text = __title__
        textbox = TextBox()
        textbox.Location = Point(0, 0)
        textbox.Text = "Please input reports text or any list of IDs to select elements"
        textbox.AutoSize = False
        textbox.Size = Size(400, 200)
        textbox.Multiline = True
        textbox.Name = 'value'
        self.Controls.Add(textbox)

        button_update = Button()
        button_update.Text = "Select"
        button_x = 8
        button_y = 200
        button_update.Location = Point(button_x, button_y)
        button_update.Click += self.form_update
        self.Controls.Add(button_update)
        self.Height = button_y + 70
        self.Width = 400
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.FormBorderStyle = FormBorderStyle.FixedDialog

    def form_update(self, sender, event):
        for control in self.Controls:
            if control.Name == 'value':
                self.value = control.Text

        parse(self.value)
        self.Close()


def run_form():
    form = pyRevitPlusForm()
    Application.Run(form)


# searching for already opened forms
err = False
for f in Application.OpenForms:
    if (f.Text == __title__):
        f.Activate()
        err = True
if err == False:
    output.set_width(400)
    output.set_height(400)
    run_form()
