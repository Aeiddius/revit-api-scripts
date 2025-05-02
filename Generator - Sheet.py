# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, ViewSheet, ViewPlan, \
                              Element, Viewport, BuiltInCategory, XYZ, \
                              FilteredElementCollector

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
target_subgroup = "Tower A"
target_discipline = [
    "Device"
] 
target_range = [4, 4]

# Functions
def main_delete_sheets() -> None:
    sheet_list: list[ViewPlan] = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
    target_sheet_list = []
    for sheet in sheet_list:
        if sheet.SheetCollectionId != ElementId(4451604): continue
        if get_parameter(sheet, "Designed By") == "Ianic-Dynamo":
            target_sheet_list.append(sheet)
            doc.Delete(sheet.Id)

def main_retrieve_keyplans() -> dict[str, ViewPlan]:
    keyplans_dict = {}
    keyplans = get_view_range("4. Dynamo", 
                              target_subgroup,
                              "Key Plan",
                              target_range,
                              True)
    for kp_view in keyplans:
        keyplans_dict[" ".join(kp_view.Name.split(" ")[1:])] = kp_view
    return keyplans_dict

# Body 
@transaction     
def start():
    
    # Get keyplans
    keyplans_dict = main_retrieve_keyplans()

    # delete previously generated sheets
    main_delete_sheets()
    discipline_count = 1
    # iterate through all of the discipline
    for discipline in target_discipline:
        views = get_view_range("2. Presentation Views",
                               target_subgroup,
                               discipline,
                               target_range,
                               True)
        titleblock_id = ElementId(1941401)
         
        for target_view in views:  
            # Create new Sheet
            new_sheet = ViewSheet.Create(doc, titleblock_id) 
            new_sheet.SheetCollectionId = ElementId(4451604)
            new_sheet.Name = target_view.Name

            # Place view 
            placed_view = Viewport.Create(doc, new_sheet.Id, 
                                          target_view.Id,
                                          XYZ(0, 0, 0))
            
            # Calculate new location point
            pvbox = placed_view.GetBoxOutline()
            max_p = pvbox.MaximumPoint
            min_p = pvbox.MinimumPoint
            
            diff = max_p.Subtract(min_p)
            new_x = (diff.X/2) + 0.4
            new_y = (diff.Y/2) + 0.25 
            placed_view.SetBoxCenter(XYZ(new_x, new_y, 0))
            
            # get keyplan
            view_name_id = " ".join(target_view.Name.split(" ")[1:])
            if view_name_id not in keyplans_dict:
                raise KeyError(f"View \"{target_view.Name}\" has no key plan.")
            keyplan_view = keyplans_dict[view_name_id]
            kp_pos = XYZ(2.7, 1.6, 0.0)  
            placed_kpview = Viewport.Create(doc, new_sheet.Id,
                                            keyplan_view.Id,
                                            kp_pos) 
  
            # Getting titleblock for parameter set
            dependent_ids = new_sheet.GetDependentElements(None)
            titleblock = ""
            for dpdnt in dependent_ids:
                elem = get_element(dpdnt)  
                if not elem.Category: continue
                if elem.Category.Id.IntegerValue == int(BuiltInCategory.OST_TitleBlocks):
                    titleblock = elem
        
            # Setting parameters
            sheet_number = "U" + target_subgroup[-1] + \
                            target_view.Name.split(" ")[1] + \
                            "." + str(discipline_count)
            unit_number = target_view.Name.split(" ")[1][2:4]
            scale = get_parameter(target_view, "View Scale")

            set_parameter(titleblock, "Unit no.", unit_number)
            set_parameter(titleblock, "View Scale", scale)
            set_parameter(new_sheet, "Sheet Number", sheet_number) 
            set_parameter(new_sheet, "Designed By", "Ianic-Dynamo") 
            
            doc.Create.PlaceGroup(new_sheet, get_element(5883378))
  
            break
        discipline_count += 1 

if activate:    
    start()  
print_member(doc)
OUT = output.getvalue()     