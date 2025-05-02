# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable


from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, CurveLoop, ViewPlan, \
                              Element, ViewDuplicateOption, \
                              FilteredElementCollector, FilledRegion

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
target_subgroup = "B"
target_discipline = {
    # "Copy": Discipline(1582582, 5747396),
    # "Lighting": Discipline(1583644, 5400826),
    "Device": Discipline(1969664, 5555552) ,
} # discipline / view family plan id / view template id
  
# Body  
@transaction     
def start():
    crop_views = get_view_range("4. Dynamo", f"Tower {target_subgroup}", "Dynamo Crop Plan")
    for discipline in target_discipline:
        for view in crop_views:
            # if "Level 4A" in view.Name: continue

            # Create New View
            new_view = ViewPlan.Create(doc,
                                       target_discipline[discipline].family_id,
                                       view.GenLevel.Id)
            new_view.CropBoxVisible = True
            new_view.CropBoxActive = True
            new_view.Name = view.Name.replace("D_Crop", f"D_{discipline}")
            new_view.ViewTemplateId = target_discipline[discipline].template_id
            new_view.CropBox = view.CropBox
            level = get_num(view.GenLevel.Name)
            set_parameter(new_view, "View Sub-Group", f"Tower {target_subgroup}") 
 
            # Get Detailed filled region
            frs = FilteredElementCollector(doc, view.Id).OfClass(FilledRegion).ToElements()
            for fr in frs:
                name: str = fr.LookupParameter("Comments").AsValueString() 
                crop_shape: CurveLoop = fr.GetBoundaries()[0]

                # Create dependent views
                new_id: ElementId = new_view.Duplicate(ViewDuplicateOption.AsDependent)
                duplicated_view: ViewPlan = doc.GetElement(new_id)
                duplicated_view.CropBoxVisible = True
                duplicated_view.CropBoxActive = True
                set_parameter(duplicated_view, "View Sub-Group", "") 

                crop_manager = duplicated_view.GetCropRegionShapeManager()
                crop_manager.SetCropShape(crop_shape)

                duplicated_view.Name = f"W_{discipline} Unit {level:02d} ({name})"
            break
if activate:  
    start() 
 
OUT = output.getvalue()  