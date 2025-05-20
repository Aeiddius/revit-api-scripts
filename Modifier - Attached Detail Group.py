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


# Parameters 


def get_dependent_views():
    views: List[ViewPlan] = get_view_range("2. Presentation Views", "b. Tower A", "Unit Rough-Ins")
    units = {}
    for view in views:
        dependent_ids = view.GetDependentViewIds()
        if not dependent_ids: continue
        num = get_num(view.Name)
        units[num] = dependent_ids
    return units
 

# Body 
@transaction      
def start(): 

    target_units = get_dependent_views()
    for lvl in target_units:
        # if lvl != 3: continue
        primary_view = ""
        print(lvl)
        # Unit
        for view_id in target_units[lvl]:
            unit_view = get_element(view_id)
            
            # Check if primary id added
            if not primary_view:
                primary_view = get_element(unit_view.GetPrimaryViewId())
            groups = collect_elements(unit_view, [BuiltInCategory.OST_IOSModelGroups])

            # Groups inside view

            for group in groups:
                reference_level = get_num(get_parameter(group, "Reference Level"))
                if reference_level != lvl: continue
                ids = list(group.GetShownAttachedDetailGroupTypeIds(primary_view))
                print(group.Name, ids)
                # break    
            print("\n")
            # break
        print("=====================\n\n")
 
if activate:     
    start()    
OUT = output.getvalue()     