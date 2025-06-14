# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, UV, ViewPlan, \
                              Element, CurveArray, SketchPlane, XYZ, \
                              FilteredElementCollector, BuiltInCategory

from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

from System.Collections.Generic import List

clr.AddReference('System')
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")

# For Outputting print to watch node
output = StringIO()
sys.stdout = output

# Scrict setup 
doc = DocumentManager.Instance.CurrentDBDocument
active_view = doc.ActiveView


def transaction(func):
    def wrapper(*args, **kwargs):
        TransactionManager.Instance.EnsureInTransaction(doc)
        func(*args, **kwargs)
        TransactionManager.Instance.TransactionTaskDone()
    return wrapper 

class Transact:
    def __init__(self):
        TransactionManager.Instance.EnsureInTransaction(doc)
    def __enter__(self):
        # print("Starting Transaction")
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        # print("Ending Transaction")
        TransactionManager.Instance.TransactionTaskDone()

# importing lib
activate = IN[1] # type: ignore
for script in IN[0]: # type: ignore
    exec(script)

# Functions and matrix definition
matrix_a: dict[str, any] = locals().get("matrix_a")
matrix_b: dict[str, any] = locals().get("matrix_b")
print_member: Callable[[any], None] = globals().get("print_member")
get_element  = globals().get("get_element")
get_elements = globals().get("get_elements")
get_element_via_parameter = globals().get("get_element_via_parameter")
get_view_range = globals().get("get_view_range")
get_num: Callable[[str], int] = globals().get("get_num")
get_parameter: Callable[[Element, str], str] = globals().get("get_parameter")
set_parameter: Callable[[Element, str, any], bool] = globals().get("set_parameter")
is_dependent: Callable[[ViewPlan], bool] = globals().get("is_dependent")
is_category_this = globals().get("is_category_this")
collect_elements = globals().get("collect_elements")

#==== Template ends here ====# 

# This script is intended to generate unit sheet views



def get_room_curve(group_elements):
  room_curve = CurveLoop()
  for id in group_elements:
    e = doc.GetElement(id)
    if isinstance(e, DetailLine):
      line = e.GeometryCurve
      room_curve.Append(line)
  return room_curve
 

   
@transaction 
def start():
    # Types
    floor_type = ElementId(7025774)
    view_template = ElementId(10342508)

    # Get levels
    source_views = get_view_range("2. Presentation Views", "b. Tower A", "Unit Rough-Ins")

    for view in source_views:
      new_view = ViewPlan.Create(doc, floor_type, view.GenLevel.Id)
 
      new_view.ViewTemplateId = view_template
      new_view.Name = view.Name.replace("-RI", "").replace("Unit ", "Ceiling ")
      new_view.CropBoxVisible = True
      new_view.CropBoxActive = True
      crop_manager = new_view.GetCropRegionShapeManager()
      crop_manager.SetCropShape(list(view.GetCropRegionShapeManager().GetCropShape())[0])
      print(view.Name)
      dependent_view_ids = view.GetDependentViewIds()
      for depview_id in dependent_view_ids:
        depview = get_element(depview_id)
        print(depview.Name, depview.Name.replace("-RI", "").replace("UNIT ", "CEILING "))
        dupli_id = new_view.Duplicate(ViewDuplicateOption.AsDependent)
        dupli_view = get_element(dupli_id)

        # Set crop shape
        crop_manager = dupli_view.GetCropRegionShapeManager()
        crop_manager.SetCropShape(list(depview.GetCropRegionShapeManager().GetCropShape())[0])

        # Set name
        dupli_view.Name = depview.Name.replace("-RI", "").replace("UNIT ", "CEILING ")
        dupli_view.CropBoxVisible = True
        dupli_view.CropBoxActive = True
      print("\n\n") 

start()

OUT = output.getvalue()



