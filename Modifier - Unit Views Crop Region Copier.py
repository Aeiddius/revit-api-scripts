# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable
from pprint import pprint
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


# Parameters 

matrix = {
    "A": matrix_a,
    "B": matrix_b
}


 
def viewname_get_unit_type(view_name):
    if "ADA" in view_name:
        x = " ".join(view_name.replace("ADA", "").split(" ")[2:3])
        return x + " ADA"
    return view_name.split(" ")[-1].rsplit("-", 1)[0]

def get_elements_by_category(view: ViewPlan, category: BuiltInCategory, isElement=False):
    elems = ""
    if not isElement:
        elems = FilteredElementCollector(doc, view.Id).OfCategory(category).WhereElementIsNotElementType().ToElementIds()
    else:
        elems = FilteredElementCollector(doc, view.Id).OfCategory(category).WhereElementIsNotElementType().ToElements()
    return elems

def organize_view_hiearchy(views):
    view_dicts = {}
    
    

    for view in views:
        dependents = view.GetDependentViewIds()
        dependent_dict = {}
        for id in dependents:
            dependent_view = get_element(id)
            key = dependent_view.Name.split(" ")[1]
            dependent_dict[key] = dependent_view

        lvl = get_num(view.Name)
        view_dicts[lvl] = {
            "primary_view": view,
            "dependent_views": dependent_dict
        }

    return view_dicts
# Body  
@transaction      
def start(): 
    target_group = "2. Presentation Views"
    target_subgroup = "b. Tower A"
    target_type = "Unit Lighting"
    
    target_units = get_view_range(target_group, target_subgroup, target_type)
    source_units = get_view_range(target_group, target_subgroup, "Unit Rough-Ins")

    target_dicts = organize_view_hiearchy(target_units)
    source_dicts = organize_view_hiearchy(source_units)

    pprint(source_dicts)

    for lvl in source_dicts:
        print(lvl)
        dependent_views = source_dicts[lvl]["dependent_views"]
        for room_no in dependent_views:
            source_view = source_dicts[lvl]["dependent_views"][room_no]
            target_view = target_dicts[lvl]["dependent_views"][room_no]

            crop_manager = target_view.GetCropRegionShapeManager()
            crop_manager.SetCropShape(list(source_view.GetCropRegionShapeManager().GetCropShape())[0])
            print(target_view.Name)
        print("\n\n")
if activate:     
    start()    
OUT = output.getvalue()      