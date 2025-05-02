# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, ViewDuplicateOption, ViewPlan, FilledRegion, CurveLoop, FilteredElementCollector

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

# Parameters
target_subgroup = "b. Tower A"
target_view_range = [2, 43 ]
target_discipline = {
#   "Lighting": "L",
  "Device Unit": "DP",
}
dont_delete_level_dependent = [2]

# Body
def main_get_curves() -> dict[str, CurveLoop]:
    crop_curves: dict[str, CurveLoop] = {}
    crop_views: List[ViewPlan] = get_view_range("4. Dynamo", 
        target_subgroup,
        "Dynamo Crop Plan") 
    for view in crop_views:
        frs = FilteredElementCollector(doc, view.Id).OfClass(FilledRegion).ToElements()
        for fr in frs:
            name: str = fr.LookupParameter("Comments").AsValueString() 
            crop_shape: CurveLoop = fr.GetBoundaries()[0]
            crop_curves[name] = crop_shape
            if name not in matrix:
                raise KeyError(f"{name} {view.Name} is an unaccounted detail group")
            # print(name, crop_shape, type(crop_shape))
    return crop_curves

def delete_dependents(view) -> None:
    dependents = view.GetDependentViewIds()
    if not dependents: return 
    for id_dpdt in dependents:
        doc.Delete(id_dpdt)
 

@transaction    
def start():
    crop_curves: dict[str, CurveLoop] = main_get_curves()
    
    for discipline in target_discipline:
        prefix = target_discipline[discipline]
        presentation_views: List[ViewPlan] = get_view_range("2. Presentation Views", 
            target_subgroup,
            discipline,
            target_view_range)
        
        print(presentation_views)
        for view in presentation_views:
            level = get_num(view.GenLevel.Name)
            if level not in dont_delete_level_dependent:
                delete_dependents(view)
             
            # uni_name is from matrix 
            for unit_name, crop_curve in crop_curves.items():
                if "BL-" in unit_name: continue
                min = matrix[unit_name].min
                max = matrix[unit_name].max

                # If current level of view is not within the 
                # current unit_name's mix/max range
                if not (min <= level <= max): continue
                if level in matrix[unit_name].exclude: continue
                
                # Duplicate
                new_id: ElementId = view.Duplicate(ViewDuplicateOption.AsDependent)
                duplicated_view: ViewPlan = doc.GetElement(new_id)
                duplicated_view.CropBoxVisible = True
                duplicated_view.CropBoxActive = True
                set_parameter(duplicated_view, "View Sub-Group", "") 

                # Set Crop Shape
                crop_manager = duplicated_view.GetCropRegionShapeManager()
                crop_manager.SetCropShape(crop_curve)
 
                # Rename
                # I dont understand how this shit works anymore
                # therefore dont fucking touch it. 
                rename = ""
                if level in matrix[unit_name].pos:
                    type_name = unit_name.split(" ")[1]
                    unit_pos = matrix[unit_name].pos[level]
                    rename = f"UNIT {level:02d}{unit_pos} {type_name}-{prefix}"
                else:
                    rename = f"UNIT {level:02d}{unit_name}-{prefix}"
                print("RENAME: ", rename)
                duplicated_view.Name = rename
    
            break

    

if activate:
    start()
 
OUT = output.getvalue()  