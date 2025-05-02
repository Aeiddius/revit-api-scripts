# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, ViewSection, ViewPlan, XYZ, CurveLoop, FilteredElementCollector

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

# importing lib
activate = IN[1] # type: ignore
for script in IN[0]: # type: ignore
    exec(script)

# Functions and matrix definition
matrix: dict[str, any] = locals().get("matrix_a")
print_member: Callable[[any], None] = globals().get("print_member")
get_element  = globals().get("get_element")
get_elements = globals().get("get_elements")
get_element_via_parameter = globals().get("get_element_via_parameter")
get_view_range = globals().get("get_view_range")
get_num: Callable[[str], int] = globals().get("get_num")
get_parameter: Callable[[Element, str], str] = globals().get("get_parameter")
set_parameter: Callable[[Element, str, any], bool] = globals().get("set_parameter")
is_dependent: Callable[[ViewPlan], bool] = globals().get("is_dependent")

#==== Template ends here ====# 

class Stairs:
    def __init__(self, target_view,num):
        self.num = num
        self.target_view = target_view

# Parameters

stairs = {
    # "B-S2": Stairs(target_view=6253016, num=91),
    # "B-S4": Stairs(target_view=6252998, num=93),
    "B-S5": Stairs(target_view=6252979, num=94),
}

# Body 
@transaction     
def start():
    for stair, strobj in stairs.items():
        target_view_manager = get_element(strobj.target_view).GetCropRegionShapeManager()
        target_view_shape = target_view_manager.GetCropShape()[0]

        view_template_id = 6253051
        view_family_Type = 6252989
        views = get_view_range("2. Presentation Views", "c. Tower B", "Device Parking")
        for view in views: 
            num = get_num(view.GenLevel.Name)
            if num == 1: continue
            
            callout = ViewSection.CreateCallout(doc, 
                                    view.Id,
                                    ElementId(view_family_Type),
                                    XYZ(0, 0, 0),
                                    XYZ(1, 1, 1)
                                    )
            callout.ViewTemplateId = ElementId(view_template_id)
            set_parameter(callout, "View Sub-Group", "d. Enlarged")

            callout_manager = callout.GetCropRegionShapeManager()
            callout_manager.SetCropShape(target_view_shape)
            callout.Name = f"{stair} B{num}{strobj.num} Stairs"
            param = callout.LookupParameter("Show in")
            param.Set(False)

            set_parameter(callout, "Title on Sheet", f"B{num}{strobj.num}")
        # break

if activate:   
    start()  
 
OUT = output.getvalue()  



    # levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
    # exclude = ["LEVEL 2 PARKING"]
    # tower = "B"
    # tower_except = ["LEVEL 1", "LEVEL 2", "LEVEL 3"]
    # max_level = 10
    # for level in levels:
    #     # Type filter
    #     if level.Name in exclude: continue
    #     if tower not in level.Name and level.Name not in tower_except: continue
        
    #     # Level filter
    #     num = get_num(level.Name)
    #     if not num: continue
    #     if num > max_level: continue

    #     print(level.Name)
    #     ViewSection.CreateCallout(doc, )