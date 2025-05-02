# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, Element, ViewPlan, FamilyInstance, BuiltInCategory, FilteredElementCollector, \
                              MEPSystem, Transform, CopyPasteOptions, ElementTransformUtils
from Autodesk.Revit.DB.Electrical import ElectricalEquipment, ElectricalSystem
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
target_group = "1. Working Views"
target_subgroup = "c. Tower B"
view_template_id = 7574536
view_family_type_id = 7007076 # device parking


def filter_source_elements(base_view):
    exception_categories = [
        int(BuiltInCategory.OST_RvtLinks),
        int(BuiltInCategory.OST_Grids),
        int(BuiltInCategory.OST_SectionBox),
        int(BuiltInCategory.OST_Cameras),
        int(BuiltInCategory.OST_Elev),
        int(BuiltInCategory.OST_Viewers),
        # int(BuiltInCategory.OST_IOSModelGroups)
        ]

    elements_source = FilteredElementCollector(doc, base_view.Id).WhereElementIsNotElementType().ToElements()
    filtered_elements = []
    added_ids = []
    
    # Filter Elements
    group_count = 0
    for e in elements_source:
        # skip weird shit that does not have a category.
        category = e.Category
        if not category: continue

        # skip banned categories
        if not category or (category and category.Id.IntegerValue in exception_categories):
            continue

        # Add model groups containing 3d models
        if category.Id.IntegerValue == int(BuiltInCategory.OST_IOSModelGroups):
            # print(f"Group {group_count}: ", e.Name)
            # Gets the instances inside the model group
            ids = e.GetMemberIds()
            for id in ids:
                grp_elem = get_element(id)
                filtered_elements.append(grp_elem)
                added_ids.append(grp_elem.Id)

                # Get Electrical System
                if isinstance(grp_elem, FamilyInstance) and grp_elem.MEPModel:
                    elec_system = grp_elem.MEPModel.GetElectricalSystems().GetEnumerator()
                    for j in elec_system:
                        if j.Id not in added_ids:
                            filtered_elements.append(j)
                            added_ids.append(j.Id)
                            
            group_count += 1
            continue
        
        # Add panels
        if isinstance(e, FamilyInstance) and isinstance(e.MEPModel, ElectricalEquipment):
            # print("Included: ", e.Name, " ", e.Id)
            filtered_elements.append(e)
            continue
        
        # Skip circuits since we added it already
        if isinstance(e, ElectricalSystem):
            continue
        
        # Filter out Switch systems
        if isinstance(e, MEPSystem):
            if (e.BaseEquipment):
                if e.BaseEquipment.Id in added_ids and e not in filtered_elements:
                    filtered_elements.append(e)
            continue

        # add anything else extra
        filtered_elements.append(e)
        added_ids.append(e.Id)


    return filtered_elements


# Body
@transaction
def start():
    include_categories = [
        int(BuiltInCategory.OST_ElectricalEquipment),
        int(BuiltInCategory.OST_IOSAttachedDetailGroups),
        int(BuiltInCategory.OST_IOSModelGroups),
        int(BuiltInCategory.OST_ElectricalEquipmentTags),
        int(BuiltInCategory.OST_ElectricalCircuit),
        int(BuiltInCategory.OST_SwitchSystem)

        # int(BuiltInCategory.OST_IOSModelGroups)
    ]

    base_view = get_element(3831030)
    target_view = get_element(5693251)

    elements_collected = FilteredElementCollector(doc, base_view.Id).WhereElementIsNotElementType().ToElements()
    elements_filtered = []

    for e in elements_collected:
        category = e.Category
        if not category or (category and category.Id.IntegerValue not in include_categories): continue
        elements_filtered.append(e)
        print(e)
    # copied_ids = ElementTransformUtils.CopyElements(
    #             base_view, 
    #             List[ElementId](e.Id for e in elements_filtered), 
    #             target_view, 
    #             Transform.Identity,
    #             CopyPasteOptions()
    #         )
    # print(copied_ids)
if activate:
    start() 
  
OUT = output.getvalue()