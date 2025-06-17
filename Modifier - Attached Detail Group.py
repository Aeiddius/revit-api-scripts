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
get_element = globals().get("get_element")
get_elements = globals().get("get_elements")
get_element_via_parameter = globals().get("get_element_via_parameter")
get_view_range = globals().get("get_view_range")
get_num: Callable[[str], int] = globals().get("get_num")
get_parameter: Callable[[Element, str], str] = globals().get("get_parameter")
set_parameter: Callable[[Element, str, any],
                        bool] = globals().get("set_parameter")
is_dependent: Callable[[ViewPlan], bool] = globals().get("is_dependent")
is_category_this = globals().get("is_category_this")
collect_elements = globals().get("collect_elements")
UnitView = locals().get("UnitView")
get_unit_key = locals().get("get_unit_key")
#==== Template ends here ====# 

# This script is intended to generate unit sheet views


# Parameters 

matrix = {
    "A": matrix_a,
    "B": matrix_b
}


def get_detail_orientation(unit, TOWER: str):

    # 01 A-2B
    for unit_name in matrix[TOWER]:
        
        # Get matrix unit
        matrix_unit = matrix[TOWER][unit_name]
        
        # Check if unit is equal to the view name
        if unit_name in unit.matrix_format:
            return matrix_unit.ortn
        
        # If it has unit pos
        if not matrix_unit.pos: continue
        for lvl in matrix_unit.pos:
            if f"{matrix_unit.pos[lvl]} {unit.unit_type}" in unit.matrix_format:
                return matrix_unit.ortn
 
    raise Exception(f"No type for view [{unit.view_name}] set in matrix") 

def show_detail(group: Group, primary_view: ViewPlan, detail_type: str):
    # get attached list
    attached_detail = list(group.GetAvailableAttachedDetailGroupTypeIds())

    # If only one detail attachment, use it
    if len(attached_detail) == 1:
        group.ShowAttachedDetailGroups(primary_view, attached_detail[0])
        return

    for detail in [get_element(i) for i in attached_detail]:
        detail_name = get_parameter(detail, "Type Name")

        if detail_type in detail_name:
            with Transact():
                group.ShowAttachedDetailGroups(primary_view, detail.Id)
                return

    raise Exception(f"No detail attached to {group.Name}")

# Body  
@transaction      
def start(): 
    TOWER = "B"
    target_group = "2. Presentation Views"
    target_type = "Unit Lighting"
    target_subgroup =  "b. Tower A" if TOWER == "A" else "c. Tower B" 
    
    target_units = get_view_range(target_group, target_subgroup, target_type)

    # Unit
    for level_view in target_units:
        dependent_views = level_view.GetDependentViewIds()
        lvl = get_num(level_view.GenLevel.Name)
        # if lvl != 5: continue

        # Iterate through dependent views
        for view_id in dependent_views:
            view = get_element(view_id)
            if "BL-" in view.Name: continue

            # if view.Name != "UNIT 0503 BPR-2BR-RI": continue
            # Name data
            unit = UnitView(view)

            # Collect Groups
            groups = collect_elements(view, [BuiltInCategory.OST_IOSModelGroups])
            detail_type = get_detail_orientation(unit, TOWER)
   
            # Check Groups
            for group in groups:
                # Guard Check
                reference_level = get_num(get_parameter(group, "Reference Level"))
                if reference_level != lvl: continue
                if unit.unit_type not in group.Name: continue
                ids = list(group.GetShownAttachedDetailGroupTypeIds(level_view))
                if ids: continue
                print(group.Name, detail_type)
                show_detail(group, level_view, detail_type)
                # group.ShowAttachedDetailGroups(primary_view, ElementId)

            # break # dependent_view iteration
 
if activate:     
    start()    
OUT = output.getvalue()     