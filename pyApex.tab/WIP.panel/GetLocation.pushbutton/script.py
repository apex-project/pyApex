# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import ElementId, Curve, XYZ, LocationPoint
from pyrevit import script, revit, forms
import math
import clr

output = script.get_output()
logger = script.get_logger()
linkify = output.linkify
doc = revit.doc
uidoc = revit.uidoc
selection = revit.get_selection()

def basis_to_angle(transform):
    vectorTran = transform.OfVector(transform.BasisX)
    null_xyz = XYZ(1,0,0)
    angle = transform.BasisX.AngleOnPlaneTo(vectorTran, null_xyz)
    return angle * (180 / math.pi)

inch_coef = 304.8
basis_x = selection[0].GetTransform().BasisX
transform = selection[0].GetTransform()
loc = selection[0].Location
# loc_point = clr.Convert(loc, LocationPoint)
print("Angle: %f" % basis_to_angle(transform))
# print("Rotation: %f, %f, %f" % (loc_point.X, loc_point.Y, loc_point.Z))