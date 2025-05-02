# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, Level, ViewPlan, ViewDuplicateOption, CurveLoop, FilteredElementCollector

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

class Discipline:
    def __init__(self, family_id, template_id):
        self.family_id = ElementId(family_id)
        self.template_id = ElementId(template_id)

# Parameters
target_group = "2. Presentation Views"
target_subgroup = "c. Tower B"
view_template_id = 7090931
view_family_type_id = 7089074 # device parking
prefix = "L"

# Body 
@transaction    
def start():

    # levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
    target_views = get_view_range(target_group, target_subgroup, "Device Parking")

    for view in target_views:
        num = get_num(view.GenLevel.Name)
        if "1B-DP" in view.Name or "BL-U" in view.Name: 
            continue
        print(num)
        # if num == 5: break
        # continue
        # Create New View  
        new_view = ViewPlan.Create(doc,
                                    ElementId(view_family_type_id),
                                    view.GenLevel.Id)
        new_view.CropBoxVisible = True
        new_view.CropBoxActive = True
        new_view.ViewTemplateId = ElementId(view_template_id)
        new_view.CropBox = view.CropBox
        set_parameter(new_view, "View Group", target_group)
        set_parameter(new_view, "View Sub-Group", target_subgroup)

        # new_view.Name = new_view.Name + prefix[discipline]
        new_view.Name = f"Parking Level {num}B-{prefix}"

        # Create Dependent views 
        view_dependents = view.GetDependentViewIds()
        for viewd in view_dependents:
            viewd_elem = get_element(viewd)
            viewd_cropmanager = viewd_elem.GetCropRegionShapeManager()

            subnew_id = new_view.Duplicate(ViewDuplicateOption.AsDependent)
            subview = get_element(subnew_id)
            subview.CropBoxVisible = True
            subview.CropBoxActive = True
            subview.CropBox = viewd_elem.CropBox
            subview_cropmanager = subview.GetCropRegionShapeManager()
            subview_cropmanager.SetCropShape(viewd_cropmanager.GetCropShape()[0])
            subview.Name = viewd_elem.Name.replace("DP", f"{prefix}")
            set_parameter(subview, "View Sub-Group", "")
            print(viewd_elem.Name.replace("DP", f"{prefix}"))
 
        
if activate:   
    start()  
 
OUT = output.getvalue()  