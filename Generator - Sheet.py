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


def main_delete_sheets() -> None:
    sheet_list: list[ViewPlan] = FilteredElementCollector(
        doc).OfClass(ViewSheet).ToElements()
    target_sheet_list = []
    for sheet in sheet_list:
        if sheet.SheetCollectionId != ElementId(4451604):
            continue
        if get_parameter(sheet, "Designed By") == "Ianic-Dynamo":
            target_sheet_list.append(sheet)
            doc.Delete(sheet.Id)


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
    TOWER = "A"
    target_type = "Unit Rough-Ins"
    target_range = [2, 4]

    target_subgroup = "b. Tower A" if TOWER == "A" else "c. Tower B"

    title_blocks = {
        "17x11": ElementId(5860782)
    }

    # Retrieve panel schedules
    panel_schedules = FilteredElementCollector(
        doc).OfClass(PanelScheduleView).ToElements()
    panel_dict = {}
    for panel in panel_schedules:
        if panel.Name[0] != "A" or panel.Name[0] != "B":
            panel_name = panel.Name.split(" ")[0]
            panel_dict[panel_name] = panel

    # Get keyplans
    keyplans_dict = {}
    keyplan_views = get_view_range("3. Utility Views",
                                   "a. Key Plan",
                                   f"Key Plan {TOWER}", dependent_only=True)
    for kp_view in keyplan_views:
        kp_name = kp_view.Name.split(" ")[2]
        kp_type = kp_view.Name.rsplit("-", 1)[-1]
        keyplans_dict[f"{kp_name}-{kp_type}"] = kp_view

    # Get target disicpline
    views = get_view_range("2. Presentation Views",
                           target_subgroup,
                           target_type,
                           target_range,
                           dependent_only=True,
                           exclude_names=["MRA", "RFA"])
    # return
    for target_view in views:

        # if target_view.Name != "UNIT 0209 A-2AR.1-RI":
        #     continue
        unit = UnitView(target_view)
        m_unit = ""
        if unit.matrix_format not in matrix[TOWER]:
            for i in matrix[TOWER]:
                if unit.unit_type not in i:
                    continue
                if unit.level not in matrix[TOWER][i].pos:
                    continue
                x = matrix[TOWER][i].pos[unit.level]
                test_name = f"{x} {unit.unit_type}"
                if test_name == unit.matrix_format:
                    # print("true!", i, unit.matrix_format)
                    m_unit = matrix[TOWER][i]
                    break
        else:
            m_unit = matrix[TOWER][unit.matrix_format]

        print(target_view.Name, m_unit.sheet_data)

        # continue
        # set_parameter(target_view, "Title on Sheet",
        #               f"UNIT {unit.unit_no} {unit.unit_type}\n{unit.view_type_full.upper()}")
        # continue
        title_block_id = title_blocks[m_unit.sheet]
        print("\n\n")
        # Create new Sheet
        new_sheet = ViewSheet.Create(doc, title_block_id)
        new_sheet.SheetCollectionId = ElementId(4451604)
        new_sheet.Name = target_view.Name

        set_parameter(new_sheet, "Sheet Group", f"Level {unit.level_str}")
        set_parameter(new_sheet, "Sheet Sub-Group", unit.full_format)
        set_parameter(new_sheet, "Sheet Number",
                      f"EA{unit.unit_no} ({unit.view_type})")
        set_parameter(new_sheet, "Sheet Name", f"{unit.unit_type}")

        # Place view
        p_viewport = Viewport.Create(doc, new_sheet.Id,
                                     target_view.Id,
                                     XYZ(0, 0, 0))
        set_parameter(p_viewport, "Family and Type",
                      ElementId(1582579))  # Title w/ Line
        p_viewport.LabelLineLength = m_unit.sheet_data["LabelLineLength"]
        p_viewport.LabelOffset = m_unit.sheet_data["LabelOffset"]
        set_parameter(p_viewport, "Title on Sheet",
                      f"UNIT {unit.unit_no} {unit.unit_type}\n{unit.view_type_full.upper()}")

        # Calculate new location point
        p_viewport.SetBoxCenter(m_unit.sheet_data["ViewportCenter"])

        # Get Panel Schedule
        # view = get_element(p_viewport.ViewId)
        panel_schedule = panel_dict[f"A{unit.unit_no}"]
        panel_instance = PanelScheduleSheetInstance.Create(
            doc, panel_schedule.Id, new_sheet)
        panel_instance.Origin = m_unit.sheet_data["PanelOrigin"]

        # Place keyplan
        kp_view = keyplans_dict[f"{unit.unit_no}-{unit.view_type}".strip()]
        print("THIS SHIT: ", f"{unit.unit_no}-{unit.view_type}")
        pprint(keyplans_dict)
        # try:
        kp_viewport = Viewport.Create(doc, new_sheet.Id,
                                      kp_view.Id,
                                      XYZ(0, 0, 0))
        set_parameter(kp_viewport, "Family and Type",
                      ElementId(1942347))  # Keyplan
        kp_viewport.SetBoxCenter(m_unit.sheet_data["KeyplanCenter"])
        # except:
        #     print("PROBLEM: ", target_view.Name)

        # break
        continue
        # Getting titleblock for parameter set
        dependent_ids = new_sheet.GetDependentElements(None)
        titleblock = ""
        for dpdnt in dependent_ids:
            elem = get_element(dpdnt)
            if not elem.Category:
                continue
            if elem.Category.Id.IntegerValue == int(BuiltInCategory.OST_TitleBlocks):
                titleblock = elem

        # Setting parameters
        sheet_number = "U" + target_subgroup[-1] + \
            target_view.Name.split(" ")[1] + \
            "." + str(discipline_count)
        unit_number = target_view.Name.split(" ")[1][2:4]
        scale = get_parameter(target_view, "View Scale")

        set_parameter(titleblock, "Unit no.", unit_number)
        set_parameter(titleblock, "View Scale", scale)
        set_parameter(new_sheet, "Sheet Number", sheet_number)
        set_parameter(new_sheet, "Designed By", "Ianic-Dynamo")

        doc.Create.PlaceGroup(new_sheet, get_element(5883378))

        break


if activate:
    start()
OUT = output.getvalue()
