# -*- coding: utf-8 -*- 
__doc__ = 'Parse elements IDs from Warnings reports\nShift+Click - do not save selection'
__title__ = 'SelManyIDs'

from scriptutils import logger
import os
import re
import os.path as op
import pickle as pl
import clr

clr.AddReferenceByPartialName('System.Windows.Forms')
clr.AddReferenceByPartialName('System.Drawing')
from Autodesk.Revit.DB import BuiltInCategory, ElementId
from System.Windows.Forms import Application, Button, Form, Label, CheckBox, DialogResult, TextBox, RadioButton, FormBorderStyle
from System.Drawing import Point, Icon, Size
from System.Collections.Generic import List
from Autodesk.Revit.UI import TaskDialog,TaskDialogCommonButtons

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

usertemp = os.getenv('Temp')
prjname = op.splitext(op.basename(doc.PathName))[0]
datafile = usertemp + '\\' + prjname + '_pySaveRevitSelection.pym'

def addtoclipboard(text):
    logger.debug('Copying IDs to clipboard')
    command = 'echo ' + text.strip() + '| clip'
    os.system(command)
    logger.debug('Copying IDs to clipboard - OK')
    
def parse(value,even=False,odd=False,saveSelection=True):
    logger.info(str([even,odd,saveSelection]))
    if(value!=None):
        value = value.strip("\n").strip(" ").strip("\t").strip("\r")
        
        value_lines = value.split("\n")
        errors = []
        ids = []
        ids_all = []
        ids_text = []
        
        for v in range(len(value_lines)):
            line_ok = False
            if(odd==True):
                if v%2 == 0:
                    line_ok = True
            elif(even==True):
                if v%2 != 0:
                    line_ok = True
            else:
                line_ok = True
            if line_ok==True:
                vl = value_lines[v]
                vl = vl.strip(" ").strip("\n").strip("\t").strip("\r")


                try:
                    _id = int(vl)
                    ids_all.append(str(int(_id)))
                    ids.append(doc.GetElement(ElementId(int(_id))).Id)
                except:
                    m = re.search(r"(id|Код)\s+([0-9]{1,})[^0-9]*", vl)
                    try:
                        _id=str(m.group(2))
                        ids_all.append(str(int(_id)))
                        ids.append(doc.GetElement(ElementId(int(_id))).Id)
                    except:
                        errors.append(vl)
        a=''
        errors.append(str(len(ids)))
        errors.append( str(len(set(ids_all))) )
        print(",".join(set(ids_all)))

        addtoclipboard(",".join(set(ids_all)))

        selection = uidoc.Selection
        selection_ids = List[ElementId](ids)
        selection.SetElementIds(selection_ids) 

        if saveSelection==True:
            selection = {elId.ToString() for elId in selection_ids}
            f = open(datafile, 'w')
            pl.dump(selection, f)
            f.close()
        if(len(errors)):
            print("Error lines", "\n".join(errors))

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

        all_items = RadioButton()
        all_items.Location = Point(10, 205)
        all_items.Text = "All"
        all_items.Name = 'all'
        all_items.Width = 50
        all_items.Checked = True
        self.Controls.Add(all_items) 

        even = RadioButton()
        even.Location = Point(60, 205)
        even.Text = "Even only"
        even.Name = 'even_only'
        even.Width = 80
        self.Controls.Add(even) 

        odd = RadioButton()
        odd.Location = Point(140, 205)
        odd.Text = "Odd only"
        odd.Name = 'odd_only'
        self.Controls.Add(odd) 

        saveSelection = CheckBox()
        saveSelection.Location = Point(260, 205)
        saveSelection.Text = "Save selection"
        saveSelection.Name = 'saveSelection'
        if not __shiftclick__:
            saveSelection.Checked = True
        self.Controls.Add(saveSelection) 

        button_update = Button()
        button_update.Text = "Select"
        button_x = 8
        button_y = 240
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
            elif control.Name == 'even_only':
                self.even_checkbox = control.Checked
            elif control.Name == 'odd_only':
                self.odd_checkbox = control.Checked
            elif control.Name == 'saveSelection':
                self.saveSelection_checkbox = control.Checked
        parse(self.value,self.even_checkbox,self.odd_checkbox,self.saveSelection_checkbox)
        self.Close()

# 
def run_form():
    form = pyRevitPlusForm()
    Application.Run(form)

#searching for already opened forms
err = False
for f in Application.OpenForms:
    if(f.Text==__title__):
        f.Activate()
        err = True
if err==False:
    run_form()

