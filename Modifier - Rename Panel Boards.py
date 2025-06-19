# Import
import clr
import sys
import time
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
activate = IN[1]  # type: ignore
for script in IN[0]:  # type: ignore
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
# ==== Template ends here ====#

# This script is intended to generate unit sheet views


# Parameters
# Parameters
matrix = {
    "A": matrix_a,
    "B": matrix_b
}

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
    TOWER = "B"
    target_subgroup = "c. Tower B"
    # target_type = "Unit Rough-Ins"
    target_type = "Unit Lighting"
    is_working = False
 
    target_units = get_view_range(
        "2. Presentation Views", target_subgroup, target_type, [1, 44], dependent_only=True, exclude_names=["MRA", "RFA"])

    for view in target_units:
        if "BL-" in view.Name: continue

        # if view.Name != "UNIT 0409 BPR-1D-L": continue

        unit = UnitView(view)
        m_unit_key = get_unit_key(unit, "B")

        unit_no = unit.unit_no
        group_format = unit.group_format


        for e in collect_elements(view, [BuiltInCategory.OST_ElectricalEquipment]):
            # location = get_parameter(e, "Location")
            param = e.LookupParameter("Panel Name")
            if not param.AsValueString():
                print("> PROBLEM: ", view.Name)
                continue
            first, rest = param.AsValueString().split(" ", 1)
            new_name = f"{TOWER}{unit_no} {rest}"
            param.Set(new_name)
            set_parameter(e, "Unit no.", f"{TOWER}{unit_no}")
            print("YES: ", new_name)

 

        # view.CropBoxActive = True 
        #  break 


if activate: 
    start()
OUT = output.getvalue()
