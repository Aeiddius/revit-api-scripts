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


def get_dependent_views(target_group: str):
    views: List[ViewPlan] = get_view_range(target_group, "b. Tower A", "Unit Rough-Ins")
    units = {}
    for view in views:
        dependent_ids = view.GetDependentViewIds()
        if not dependent_ids: continue
        num = get_num(view.Name)
        units[num] = dependent_ids
    return units
 
def viewname_get_unit_type(view_name):
    return view_name.split(" ")[-1].rsplit("-", 1)[0]
    
# Body 
@transaction      
def start(): 
    TOWER = "A"

    include_categories = [
        int(BuiltInCategory.OST_ElectricalEquipment),
        int(BuiltInCategory.OST_IOSModelGroups),
        int(BuiltInCategory.OST_ElectricalCircuit), 
        int(BuiltInCategory.OST_SwitchSystem),
        # int(BuiltInCategory.OST_ElectricalEquipmentTags), 
    ]
    

    target_units = get_dependent_views("2. Presentation Views")
    for level in target_units:
        for tview in target_units[level]:
            
            unit_view = get_element(tview)
            print("> ", level, unit_view.Name)
            element_collector = FilteredElementCollector(doc, unit_view.Id)
            group_to_hide = []
            element_to_hide = []
            unit_type = viewname_get_unit_type(unit_view.Name)
            unit_Type_1 = f"(Type {unit_type})"

            room_name = TOWER+unit_view.Name.split(" ")[1]


            for e in element_collector.WhereElementIsNotElementType().ToElements():
                if is_category_this(e, BuiltInCategory.OST_IOSModelGroups):
                    if unit_Type_1 not in e.Name and e.CanBeHidden:
                        group_to_hide.append(e)
                if is_category_this(e, BuiltInCategory.OST_ElectricalEquipment):
                    if room_name not in e.Name and e.CanBeHidden:
                        element_to_hide.append(e.Id)

            print("\n============\n") 
            for e in group_to_hide:
                unit_view.HideElements(List[ElementId](e.GetMemberIds() + element_to_hide))

 
if activate:     
    start()   
OUT = output.getvalue()     