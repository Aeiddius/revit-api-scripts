# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, UV, ViewPlan, \
    Element, CurveArray, SketchPlane, TemporaryViewMode, \
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
# ==== Template ends here ====#

# This script is intended to generate unit sheet views


# Parameters


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
    # target_type = "Unit Rough-Ins"
    target_type = "Unit Device"

    target_units = get_view_range(
        "2. Presentation Views", target_subgroup, target_type, dependent_only=True, exclude_names=["MRA", "RFA"])

    for view in target_units:
        print(view.Name)
        unit = UnitView(view)
        element_to_reveal = []
        view.EnableRevealHiddenMode()
        for e in collect_elements(view, [BuiltInCategory.OST_ElectricalEquipment]):

            if f"{TOWER}{unit.unit_no}" in e.Name:
                element_to_reveal.append(e.Id)

        if element_to_reveal != []:
            view.UnhideElements(List[ElementId](element_to_reveal))
            print("Revealed: ", element_to_reveal)
        view.DisableTemporaryViewMode( TemporaryViewMode.RevealHiddenElements )


if activate:
    start()
OUT = output.getvalue()
