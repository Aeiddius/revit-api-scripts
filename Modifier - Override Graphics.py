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


def get_elements_by_category(view: ViewPlan, category: BuiltInCategory, isElement=False):
    elems = ""
    if not isElement:
        elems = FilteredElementCollector(doc, view.Id).OfCategory(
            category).WhereElementIsNotElementType().ToElementIds()
    else:
        elems = FilteredElementCollector(doc, view.Id).OfCategory(
            category).WhereElementIsNotElementType().ToElements()
    return elems


def apply_override(view: ViewPlan, category: BuiltInCategory, override: OverrideGraphicSettings):
    electrical_fixture_tag = get_elements_by_category(view, category)
    for elem in electrical_fixture_tag:
        view.SetElementOverrides(elem, override)


def batch_override(view: ViewPlan, target_type: str, override: OverrideGraphicSettings):
    if target_type == "Unit Lighting":
        apply_override(
            view, BuiltInCategory.OST_ElectricalFixtureTags, override)
        apply_override(view, BuiltInCategory.OST_LightingDeviceTags, override)

    if target_type == "Unit Device":
        apply_override(view, BuiltInCategory.OST_LightingFixtureTags, override)
        apply_override(view, BuiltInCategory.OST_FireAlarmDeviceTags, override)

# Body


@transaction
def start():
    target_group = "2. Presentation Views"
    target_subgroup = "b. Tower A"
    target_type = "Unit Lighting"
    # target_type = "Unit Device"

    target_units = get_dependent_views(
        target_group, target_subgroup, target_type)

    graphics = OverrideGraphicSettings()
    graphics.SetProjectionLineColor(Color(0, 128, 64))
    graphics.SetHalftone(True)
    for lvl in target_units:

        for view_id in target_units[lvl]:
            unit_view = get_element(view_id)
            print(unit_view.Name)

            batch_override(unit_view, target_type, graphics)

            # mechanical_tags = get_elements_by_category(unit_view, BuiltInCategory.OST_MechanicalEquipmentTags, True)
            # for elem in mechanical_tags:
            #     if "ACCU" in elem.TagText:
            #         graphics.SetSurfaceTransparency(100)
            #         unit_view.SetElementOverrides(elem.Id, graphics)

    target_units = get_view_range(target_group, target_subgroup, target_type)
    for view in target_units:

        batch_override(view, target_type, graphics)


if activate:
    start()
OUT = output.getvalue()
