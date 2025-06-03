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

matrix = {
    "A": matrix_a,
    "B": matrix_b
}


def get_dependent_views(target_group, target_subgroup, target_type):
    views: List[ViewPlan] = get_view_range(
        target_group, target_subgroup, target_type)
    units = {}
    for view in views:
        dependent_ids = view.GetDependentViewIds()
        if not dependent_ids:
            continue
        num = get_num(view.Name)
        units[num] = dependent_ids
    return units


def viewname_get_unit_type(view_name):
    if "ADA" in view_name:
        x = " ".join(view_name.replace("ADA", "").split(" ")[2:3])
        return x + " ADA"
    return view_name.split(" ")[-1].rsplit("-", 1)[0]


def get_unit_type(view_name, TOWER):
    view_unit_name = view_name.split(" ", 1)[-1].rsplit('-', 1)[0][2:].strip()
    print("?>???>>  ", view_unit_name)
    set_type = "x"
    for unit_name in matrix[TOWER]:
        # print(unit_name)
        unit = matrix[TOWER][unit_name]

        if unit_name in view_unit_name:
            set_type = unit.ortn
            print("TYPE: ", unit_name)
            return set_type
        elif unit.pos:
            for lvl in unit.pos:
                unit_name_2 = unit.pos[lvl] + " " + unit_name.split(" ")[1]
                if unit_name_2 in view_unit_name:
                    set_type = unit.ortn
                    return set_type
    if set_type == "x":
        print("NO UNIT FOR: ", view_unit_name)
        raise Exception(f"No type for view [{view_name}] set in matrix")


# Body
@transaction
def start():
    target_group = "2. Presentation Views"
    target_subgroup = "b. Tower A"
    target_type = "Enlarged Rough-Ins"

    target_units = get_view_range(target_group, target_subgroup, target_type)
    for view in target_units:
        groups = collect_elements(view, [BuiltInCategory.OST_IOSModelGroups])

        # Groups inside view
        for group in groups:
            reference_level = get_num(get_parameter(group, "Reference Level"))
            if reference_level != lvl:
                continue
            if unit_Type_1 not in group.Name:
                continue
            ids = list(group.GetShownAttachedDetailGroupTypeIds(primary_view))
            if ids:
                continue

            attached_detail = list(
                group.GetAvailableAttachedDetailGroupTypeIds())
            if len(attached_detail) == 1:
                group.ShowAttachedDetailGroups(
                    primary_view, attached_detail[0])
                continue
            else:
                attached = False
                for detail in attached_detail:
                    detail_elem = get_element(detail)
                    detail_name = get_parameter(detail_elem, "Type Name")

                    if set_type in detail_name:
                        with Transact():
                            group.ShowAttachedDetailGroups(
                                primary_view, detail_elem.Id)
                            attached = True
                            continue

                    # Disposal
                    detail_elem.Dispose()
                    del detail_name
                if not attached:
                    raise Exception(f"No detail attached to {group.Name}")


if activate:
    start()
OUT = output.getvalue()
