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
        TransactionManager.Instance.ForceCloseTransaction()
        TransactionManager.Instance.EnsureInTransaction(doc)
        func(*args, **kwargs)
        TransactionManager.Instance.TransactionTaskDone()
        # doc.Regenerate()
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

# This script is intended to generate unit sheet views


# Parameters 
target_group = "4. Dynamo" 

target_range = [1, 43]      

 
# Body 
@transaction      
def start(): 
    # Get list of views
    device_views = get_view_range("2. Presentation Views",
                        "b. Tower A",
                        "Enlarged Device")
    roughins_views = get_view_range("2. Presentation Views",
                        "b. Tower A",
                        "Enlarged Rough-Ins")
    
    dict_rough_ins = {}
    dict_devices = {}
    for view in roughins_views:
        num = get_num(view.Name)
        dict_rough_ins[num] = view
    
    for view in device_views:
        num = get_num(view.Name)
        dict_devices[num] = view
    
    for lvl_num in dict_devices:
        if not lvl_num: continue
        if lvl_num <=3: continue
        
        view_rins = dict_rough_ins[lvl_num]
        north_view_rins = get_element(view_rins.Duplicate(ViewDuplicateOption.AsDependent))
        south_view_rins = get_element(view_rins.Duplicate(ViewDuplicateOption.AsDependent))

        north_view_rins.Name = north_view_rins.Name.replace("- Dependent 1", "NORTH")
        south_view_rins.Name = south_view_rins.Name.replace("- Dependent 2", "SOUTH")

        dependent_views = dict_devices[lvl_num].GetDependentViewIds()
        for dpdnt_id in dependent_views:
            dpdnt_view = get_element(dpdnt_id)
            if "NORTH" in dpdnt_view.Name:
                crop_manager = north_view_rins.GetCropRegionShapeManager()
                crop_manager.SetCropShape(list(dpdnt_view.GetCropRegionShapeManager().GetCropShape())[0])
            if "SOUTH" in dpdnt_view.Name:
                crop_manager = south_view_rins.GetCropRegionShapeManager()
                crop_manager.SetCropShape(list(dpdnt_view.GetCropRegionShapeManager().GetCropShape())[0])
        

if activate:     
    start()   
OUT = output.getvalue()     