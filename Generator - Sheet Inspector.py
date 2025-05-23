# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable
from pprint import pprint

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, ViewSheet, ViewPlan, \
    Element, Viewport, BuiltInCategory, XYZ, \
    FilteredElementCollector
from Autodesk.Revit.DB.Electrical import PanelScheduleView, PanelScheduleSheetInstance

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
        TransactionManager.Instance.ForceCloseTransaction()
        TransactionManager.Instance.EnsureInTransaction(doc)
        func(*args, **kwargs)
        TransactionManager.Instance.TransactionTaskDone()
        # doc.Regenerate()
    return wrapper


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
# Parameters
matrix = {
    "A": matrix_a,
    "B": matrix_b
}

# Functions


class Offset:

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class UnitView:
    view_types = {
        "L": "Lighting",
        "RI": "Rough-Ins",
        "D": "Device",
    }

    def __init__(self, view: ViewPlan):
        self.view = view
        self.level: int = 0  # ex. 2
        self.level_str: str = ""  # ex. 02
        self.unit_no: str = ""  # 0201
        self.unit_pos: str = ""  # 01
        self.unit_type: str = ""    # ex. A-2B
        self.view_type: str = ""  # RI/L/D
        self.view_type_full: str = ""  # ex. Lighting/Rough-Ins/Device

        self.group_format: str = ""  # ex. (Type A-2B)
        self.matrix_format: str = ""  # ex. 01 A-2B
        self.full_format: str = ""  # ex. 0201 A-2B

        self._initialize()

    def _initialize(self):
        # view.Name = UNIT 0203 A-2AR-L

        # ["0203", "A-2AR-L"]
        x = self.view.Name.replace("UNIT ", "").split(" ")
        self.unit_no = x[0].strip()  # "0203"

        # ["A-2AR", "L"]
        y = x[1].rsplit("-", 1)
        self.unit_type = y[0].strip()  # "A-2AR"
        self.view_type = y[1].strip()  # L
        self.view_type_full = UnitView.view_types[y[1]].strip()  # "Lighting"
        self.group_format = f"(Type {y[0]})".strip()

        self.unit_pos = self.unit_no[2:].strip()
        self.level = int(self.unit_no[:2])
        self.level_str = self.unit_no[:2].strip()

        # "01 A-2B"
        self.matrix_format = f"{self.unit_pos} {self.unit_type}"
        # "0201 A-2B"
        self.full_format = f"{self.unit_no} {self.unit_type}"

    def print_data(self):
        print("View Name: ", self.view.Name)
        print("  Level: ", self.level_str)
        print("  Unit no.: ", self.unit_no)
        print("  Unit pos.: ", self.unit_pos)
        print("  Unit Type: ", self.unit_type)
        print("  Unit View Type: ", self.view_type)
        print("  Unit Group Format: ", self.group_format)
        print("  Unit Matrix Format: ", self.matrix_format)


def calculate_viewport_pos(p_viewport, xy: Offset):
    pvbox = p_viewport.GetBoxOutline()
    max_p = pvbox.MaximumPoint
    min_p = pvbox.MinimumPoint

    diff = max_p.Subtract(min_p)
    new_x = (diff.X/2) + xy.x
    new_y = (diff.Y/2) + xy.y
    p_viewport.SetBoxCenter(XYZ(new_x, new_y, 0))

# Body


@transaction
def start():
    # active_view

    ViewportCenter = ""
    LabelLineLength = ""
    LabelOffset = ""
    PanelOrigin = ""
    KeyplanCenter = ""

    panel_schedule = collect_elements(
        active_view, [BuiltInCategory.OST_PanelScheduleGraphics])[0]
    panel_origin = panel_schedule.Origin

    viewports = collect_elements(active_view, [BuiltInCategory.OST_Viewports])
    viewports.reverse()
    for viewport in viewports:
        viewport_type = get_parameter(viewport, "Family and Type")
        if "Title w/ Line" in viewport_type:
            ViewportCenter = viewport.GetBoxCenter()
            LabelLineLength = viewport.LabelLineLength
            LabelOffset = viewport.LabelOffset
        if "Keyplan" in viewport_type:
            KeyplanCenter = viewport.GetBoxCenter()
    # print('sheet="17x11",')
    print("sheet_data={")
    print(f'"LabelLineLength": {LabelLineLength},')
    print(f'"LabelOffset": XYZ{LabelOffset},')
    # print(f'"LabelOffset": XYZ(0.636081024, -0.088131822, 0.000000000),')
    print(f'"PanelOrigin": XYZ{panel_origin},')
    print(f'"ViewportCenter": XYZ{ViewportCenter},')
    print(f'"KeyplanCenter": XYZ{KeyplanCenter},')
    print("}")


if activate:
    start()
OUT = output.getvalue()

