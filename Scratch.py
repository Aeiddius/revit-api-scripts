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
matrix: dict[str, any] = locals().get("matrix_a")
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

# ==== Template ends here ====#


class Discipline:
    def __init__(self, family_id, template_id):
        self.family_id = ElementId(family_id)
        self.template_id = ElementId(template_id)

# Parameters


a3_spares = [
    [14, 1],
    [16, 6],
    [17, 6],
    # [15, 1],
]
a3_double_pole = [[14, 1]]
# Body ss


@transaction
def start():

    views = get_view_range("2. Presentation Views", "c. Tower B", "Unit Device")
    for view in views:
        enums = [
            PlanViewPlane.BottomClipPlane,
            PlanViewPlane.CutPlane,
            PlanViewPlane.TopClipPlane,
            PlanViewPlane.UnderlayBottom,
            PlanViewPlane.ViewDepthPlane,
        ]



        try:
            source_vr = view.GetViewRange()

            for plane in enums:
        
        
                s_level_id = source_vr.GetLevelId(plane)

                if int(s_level_id.ToString()) < 0: continue

                source_vr.SetLevelId(plane, view.GenLevel.Id)
    
            view.SetViewRange(source_vr)
        except:
            print(view.Name)


    # original = get_element(10549621)
    # target = get_element(10549868)

    # target.Origin = original.Origin

    # return
    # placed_view = get_element(10551907)
    # placed_view.SetBoxCenter(XYZ(0.765528942, 1.779766219, -0.222395833))
    # Horiontal
    # placed_view.SetBoxCenter(XYZ(0.727590417, 0.186369829, -0.241145833))

    # Original
    # placed_view.SetBoxCenter(XYZ(0.737794410, 1.236961806, 0.358854167))


# (0.751355251, 0.195793393, -0.166145833)
    # placed_view.Origin = XYZ(0.058865373, 1.389748524, 0.000000000)
    # placed_view.Origin = XYZ(0.058865373, 0.387171030, 0.000000000)
    # set_parameter(placed_view, "Family and Type", ElementId(1942347))
    # Calculate new location point
    # pvbox = placed_view.GetBoxOutline()
    # max_p = pvbox.MaximumPoint
    # min_p = pvbox.MinimumPoint

    # diff = max_p.Subtract(min_p)
    # new_x = (diff.X/2) + 0
    # new_y = (diff.Y/2) - 0.07
    # placed_view.SetBoxCenter(XYZ(new_x, new_y, 0))

    # template_a1 = get_element(7178103)
    # template_a2 = get_element(7123164)
    # # PanelScheduleView.CreateInstanceView(doc, template_a1.Id, ElementId(8693954))

    # ps_view = get_element(9561093)
    # for sp in a3_spares:
    #     r = sp[0]
    #     c = sp[1]
    #     ps_view.AddSpare(r, c)

    #     es = ps_view.GetCircuitByCell(r, c)
    #     set_parameter(es, "Load Name", "SPARE")
    #     if sp in a3_double_pole:
    #         set_parameter(es, "Number of Poles", 2)

if activate:
    start()
OUT = output.getvalue()
