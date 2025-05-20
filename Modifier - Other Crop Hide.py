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


#==== Template ends here ====# 

# This script is intended to generate unit sheet views


# Parameters 


def get_dependent_views(target_group: str, target_subgroup: str, target_type: str):
    views: List[ViewPlan] = get_view_range(target_group, target_subgroup, target_type )
    units = {}
    for view in views:
        dependent_ids = view.GetDependentViewIds()
        if not dependent_ids: continue
        num = get_num(view.Name)
        units[num] = dependent_ids
    return units
 
def viewname_get_unit_type(view_name):
    if "ADA" in view_name:
        x = " ".join(view_name.replace("ADA", "").split(" ")[2:3])
        return x + " ADA"
    return view_name.split(" ")[-1].rsplit("-", 1)[0]

def filter_members(e, view):
    element_to_hide = []
    for grp_elem_id in e.GetMemberIds():
        grp_elem = get_element(grp_elem_id)
        if grp_elem.CanBeHidden(view):
            element_to_hide.append(grp_elem_id)
        grp_elem.Dispose()
    return element_to_hide
# Body 
@transaction      
def start(): 
    TOWER = "A"
    target_subgroup = "b. Tower A"
    target_type = "Unit Rough-Ins"
    target_type = "Unit Device"

    target_units = get_dependent_views("2. Presentation Views", target_subgroup, target_type)
    for level in target_units:
        # if level != 43: continue
        for tview in target_units[level]:
            
            unit_view = get_element(tview) 
            element_collector = FilteredElementCollector(doc, unit_view.Id)
            element_to_hide = []
            unit_type = viewname_get_unit_type(unit_view.Name)
            unit_Type_1 = f"(Type {unit_type})" 

            room_name = TOWER+unit_view.Name.split(" ")[1]
            
            print(unit_view.Name, "| ", unit_type)
            # continue
            for e in element_collector.WhereElementIsNotElementType().ToElements():
                if is_category_this(e, BuiltInCategory.OST_IOSModelGroups):
                    if unit_Type_1 not in e.Name and e.CanBeHidden(unit_view):
                        to_hide = filter_members(e, unit_view)
                        element_to_hide += to_hide
                if is_category_this(e, BuiltInCategory.OST_ElectricalEquipment):
                    if room_name not in e.Name and e.CanBeHidden:
                        element_to_hide.append(e.Id)
                # if is_category_this(e, BuiltInCategory.OST_IOSAttachedDetailGroups):
                #     x = get_element(e.AttachedParentId)
                #     if x.Name != unit_Type_1:
                #         to_hide = filter_members(e)
                #         element_to_hide += to_hide
   

              
            if len(element_to_hide) == 0:
                print("Zero Elements to hide")
                print("---------------------------------\n\n\n")
                continue

            for elem in element_to_hide:
                try:
                    unit_view.HideElements(List[ElementId]([elem]))
                except:
                    print(f"Error: {elem}")
                    continue
                print("Sucesss ", elem)
            print("---------------------------------\n\n\n")
if activate:     
    start()   
OUT = output.getvalue()     