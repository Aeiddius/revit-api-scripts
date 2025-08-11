# Import
from System.Linq import Enumerable
import System
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, PlanViewPlane, SectionType, ViewPlan, FilledRegion, CurveLoop, FilteredElementCollector
from Autodesk.Revit.DB.Electrical import PanelScheduleView, ElectricalSystem
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

from System.Collections.Generic import List
clr.AddReference("System.Core")

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


class Discipline:
    def __init__(self, family_id, template_id):
        self.family_id = ElementId(family_id)
        self.template_id = ElementId(template_id)








@transaction
def start():
    # Parameters

    spares = [
        [14, 1],
        [7, 6],
        [13, 6],
        [15, 6],

    ]
    spares_double = [
        [14, 1]
    ]

    ps_view = active_view
    for sp in spares:
        r = sp[0]
        c = sp[1]
        ps_view.AddSpare(r, c)

        es = ps_view.GetCircuitByCell(r, c)
        set_parameter(es, "Load Name", "SPARE")
        if sp in spares_double:
            set_parameter(es, "Number of Poles", 2)

if activate:
    start()
OUT = output.getvalue()
