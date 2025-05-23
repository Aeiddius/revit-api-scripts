# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable
from pprint import pprint

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, ViewSheet, ViewPlan, \
    Element, Viewport, BuiltInCategory, XYZ, \
    DatumExtentType , DatumEnds
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


# Body


@transaction
def start():
    source_view = get_element(3830822)
    target_view = get_element(5693377)

    source_grids = collect_elements(source_view, [BuiltInCategory.OST_Grids])

    grid_dict = {}
    for i in source_grids:
        grid_dict[i.Id] = i


    for g_id in grid_dict:
        grid = grid_dict[g_id]
        # grid.PropagateToViews(source_view, List[ElementId]([target_view.Id]))
        # continue
        # Set the fuckign bubble
        for datum in [DatumEnds.End0, DatumEnds.End1]:
            bubble_seen = grid.IsBubbleVisibleInView(datum, source_view)
            if bubble_seen:
                grid.ShowBubbleInView(datum, target_view)
            else:
                grid.HideBubbleInView(datum, target_view)

        curves = grid.GetCurvesInView(DatumExtentType.ViewSpecific, source_view)[0]

        print(grid.Name, curves, curves.ApproximateLength)
        # grid.SetCurveInView(DatumExtentType.ViewSpecific, target_view, curves)

        print("\n")


if activate:
    start()
OUT = output.getvalue() 
