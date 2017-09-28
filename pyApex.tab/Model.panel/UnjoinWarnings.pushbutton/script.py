# -*- coding: utf-8 -*- 
__doc__ = 'Unjoin selected elements by pairs from warnings text'
__title__ = 'Unjoin Warnings'

from scriptutils import logger
import os
import re
import os.path as op
import pickle as pl
import clr

from Autodesk.Revit.DB import BuiltInCategory, ElementId, JoinGeometryUtils, Transaction
clr.AddReferenceByPartialName('System.Windows.Forms')
clr.AddReferenceByPartialName('System.Drawing')
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

def unjoin(pairs):
    # print(pairs)

    # rng = range(len(selection))
    # checked_pairs = []
    # joined_pairs = []
    c = 0

    # for x in rng:
    #     for y in rng:
    #         if x == y:
    #             continue
    #         _p = sorted([x,y])
    #         _t = (_p[0],_p[1])
    #         if _t in checked_pairs:
    #             continue

    #         checked_pairs.append(_t)
    #         eid1 = selection[_p[0]]
    #         eid2 = selection[_p[1]]
    #         e1,e2 = doc.GetElement(eid1),doc.GetElement(eid2)
    #         joined = JoinGeometryUtils.AreElementsJoined(doc,e1,e2)
    #         if joined:
    #             joined_pairs.append((e1,e2))

    if len(pairs) > 0:
        t = Transaction(doc)
        t.Start("UnjoinSelected")
        for p in pairs:
            e1 = doc.GetElement(ElementId(p[0]))
            e2 = doc.GetElement(ElementId(p[1]))
            joined = JoinGeometryUtils.AreElementsJoined(doc,e1,e2)
            if joined:

                JoinGeometryUtils.UnjoinGeometry(doc,e1,e2)
                c+=1
        t.Commit()
    TaskDialog.Show("R","%d пар элементов разъединены" % c)


    
def parse(value,even=False,odd=False,saveSelection=True):
    logger.info(str([even,odd,saveSelection]))
    if(value!=None):
        value = value.strip("\n").strip(" ").strip("\t").strip("\r")
        
        value_lines = value.split("\n")
        errors = []
        ids = []
        ids_all = []
        ids_text = []
        pair = []
        pairs = []
        for v in range(len(value_lines)):
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

                    if v%2 == 0:
                        pair =[]
                    pair.append(int(_id))
                    if v%2 != 0:
                        pairs.append(pair)

                    ids_all.append(str(int(_id)))
                    ids.append(doc.GetElement(ElementId(int(_id))).Id)
                except:
                    errors.append(vl)
        a=''
        errors.append(str(len(ids)))
        errors.append( str(len(set(ids_all))) )
        print(",".join(set(ids_all)))

        # addtoclipboard(",".join(set(ids_all)))

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

        unjoin(pairs)
        # print(pairs)


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
        parse(self.value)
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
