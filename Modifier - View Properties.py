# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable
from pprint import pprint

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, ViewSheet, ViewPlan, \
    Element, Viewport, BuiltInCategory, XYZ, \
    DatumExtentType, DatumEnds
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
UnitView = locals().get("UnitView")

# ==== Template ends here ====#

# This script is intended to generate unit sheet views


# Parameters
# Parameters
matrix = {
    "A": matrix_a,
    "B": matrix_b
}

# Functions


# Body

def aligngrids(source_view, target_view):
    source_grids = collect_elements(source_view, [BuiltInCategory.OST_Grids])
    # crop_curve = target_view.GetCropRegionShapeManager().GetCropShape()[0]
    elemens = [i.Id for i in collect_elements(target_view, [BuiltInCategory.OST_Grids])]

    grid_dict = {}
    for i in source_grids:
        grid_dict[i.Id] = i

    for g_id in grid_dict:
        if g_id not in elemens: continue
        grid = grid_dict[g_id]


        # Set bubbles
        for datum in [DatumEnds.End0, DatumEnds.End1]:
            bubble_seen = grid.IsBubbleVisibleInView(datum, source_view)
 
            if bubble_seen:
                grid.ShowBubbleInView(datum, target_view)
            else:
                grid.HideBubbleInView(datum, target_view)


        # Set Curve Length 
        srcCurve = grid.GetCurvesInView(
            DatumExtentType.ViewSpecific, source_view)[0]
        trgCurve = grid.GetCurvesInView(
            DatumExtentType.ViewSpecific, target_view)[0]

        p0 = srcCurve.GetEndPoint(0) 
        p1 = srcCurve.GetEndPoint(1)

        proj0 = trgCurve.Project(p0).XYZPoint
        proj1 = trgCurve.Project(p1).XYZPoint

        boundSeg = Line.CreateBound(proj0, proj1)

        grid.SetCurveInView(DatumExtentType.ViewSpecific,
                            target_view, boundSeg)

def set_crop_region(source_view, target_view):
    try:
        target_manager = target_view.GetCropRegionShapeManager()
        source_manager = source_view.GetCropRegionShapeManager()
  
        target_manager.SetCropShape(source_manager.GetCropShape()[0])
        target_manager.LeftAnnotationCropOffset = source_manager.LeftAnnotationCropOffset
        target_manager.RightAnnotationCropOffset = source_manager.RightAnnotationCropOffset
        target_manager.TopAnnotationCropOffset = source_manager.TopAnnotationCropOffset
        target_manager.BottomAnnotationCropOffset = source_manager.BottomAnnotationCropOffset
    except:
        print("FAILED CROP REGION", target_view.Name, "|", source_view.Name)


def set_view_range(source_view, target_view):
    source_vr = source_view.GetViewRange()
    try:
        target_view.SetViewRange(source_vr)
    except:
        print("FAILED VIEW RANGE: ", target_view.Name, "|", source_view.Name)

 
@transaction 
 
def start():
    TOWER = "B"
    views = get_view_range("2. Presentation Views",
                           "c. Tower B", "Unit Lighting", dependent_only=True)
    working_views = get_view_range("1. Working Views",
                                   "c. Tower B", "Unit Rough-Ins", dependent_only=True)
    w_views_dict = {}
    for w_view in working_views:
        name = w_view.Name.split("(")[1].replace(")", "").strip()
        w_views_dict[name] = w_view

    for view in views:
        if "BL-" in view.Name: continue
        unit = UnitView(view)
        # if unit.level == 2: continue
        # if view.Name != "UNIT 0803 BPR-2BR-L": continue
        m_unit_key = ""
        if unit.matrix_format not in matrix[TOWER]:
            for i in matrix[TOWER]:
                if unit.unit_type not in i:
                    continue
                if unit.level not in matrix[TOWER][i].pos:
                    continue
                x = matrix[TOWER][i].pos[unit.level]
                test_name = f"{x} {unit.unit_type}"
                if test_name == unit.matrix_format:
                    m_unit_key = i
                    break 
        else:
            m_unit_key = unit.matrix_format

        # try:
        print(view.Name, "|", unit.unit_type)
        source_view = w_views_dict[m_unit_key]
        aligngrids(source_view, view)
        set_crop_region(source_view, view) 
        set_view_range(source_view, view)
        # except:
        #     print(view.Name, "|", unit.unit_type)

    # pprint(w_views_dict)  

if activate:
    start()
OUT = output.getvalue()
#  s s s  s a s s