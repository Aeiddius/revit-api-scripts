# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, UV, ViewPlan, \
                              Element, CurveArray, OverrideGraphicSettings, ViewDuplicateOption, \
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
tower = "A" 


# Body 
@transaction     
def start():
    tower_code = "b" if tower is "A" else "b"
    tower_subgroup = f"{tower_code}. Tower {tower}"

    existing = get_view_range("3. Utility Views", "a. Key Plan", f"Key Plan {tower}")
    if existing:
        for view in existing:
            doc.Delete(view.Id)

    master_views = get_view_range("4. Dynamo", tower_subgroup, "Dynamo Key Plan")

    for view in master_views: 
 
        # Create new duplicate
        new_id: ElementId = view.Duplicate(ViewDuplicateOption.WithDetailing)
        duplicated_view: ViewPlan = doc.GetElement(new_id)
        duplicated_view.ViewTemplateId = ElementId(3858363)
        duplicated_view.CropBoxVisible = True
        duplicated_view.CropBoxActive = True

        # Set name
        level = get_num(duplicated_view.GenLevel.Name)
        duplicated_view.Name = f"KEY PLAN {level}{tower}"

        # Set view grop and type
        set_parameter(duplicated_view, "View Group", "3. Utility Views")
        set_parameter(duplicated_view, "View Sub-Group", "a. Key Plan") 
        params = duplicated_view.GetParameters("Type")
        params[0].Set(ElementId(1942334))
        
        # Get texts
        text_dict = {}
        text_notes = FilteredElementCollector(doc, duplicated_view.Id).OfCategory(BuiltInCategory.OST_TextNotes).ToElements()
        for text in text_notes:
            text_dict[text.Text.strip()] = text
        print(text_dict)

        # Get filled region
        fr_dict = {}
        filled_region = FilteredElementCollector(doc, duplicated_view.Id).OfCategory(BuiltInCategory.OST_DetailComponents).ToElements()
        for fr in filled_region:
            comment = get_parameter(fr, "Comments")
            fr_dict[comment] = fr
 
        for fr_name, fr_object in fr_dict.items():
            if level == 2 and "BL-" in fr_name: continue
            for prefix in ["DP", "L", "KB"]:
                text_value = fr_name.split(" ")[0]

                subnew_id: ElementId = duplicated_view.Duplicate(ViewDuplicateOption.AsDependent)
                subview = get_element(subnew_id)
                subview.CropBoxVisible = False
                subview.CropBoxActive = True
                # Set text notes to half-tone
                for txt in text_dict:
                    if text_value == txt: continue
                    override = OverrideGraphicSettings()
                    override.SetHalftone(True)
                    subview.SetElementOverrides(text_dict[txt].Id, override)
                
                to_hide = List[ElementId]([fr_dict[fr].Id for fr in fr_dict if fr != fr_name])
                subview.HideElements(to_hide)

                # Setting subview name
                new_name = ""
                if "BL-" in fr_name:
                    bl_name = fr_name.replace("LIVE", "").replace("RESI", "").strip()
                    new_name = f"KEY PLAN {bl_name}-{prefix}"
                else:
                    new_name = f"KEY PLAN {level:02d}{fr_name}B-{prefix}"
                print(new_name)
                subview.Name = new_name
        

            
                 
if activate:      
    start()    
OUT = output.getvalue()      