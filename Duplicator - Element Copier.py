# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, Element, ViewPlan, FamilyInstance, BuiltInCategory, FilteredElementCollector, \
                              MEPSystem, Transform, CopyPasteOptions, ElementTransformUtils, Group
from Autodesk.Revit.DB.Electrical import ElectricalEquipment, PanelScheduleView
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
is_category_this = globals().get("is_category_this")

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


matrix = {
    "01 A-2A": "Right",
    "05 A-1BR": ""
}

workset = {
    "RCP": 783,
    "Power": 784,
    "Fire": 785,
    "Panel": 835,
    "HMC": 778,
}

# Body
@transaction
def start():
    include_categories = [
        int(BuiltInCategory.OST_ElectricalEquipment),
        # int(BuiltInCategory.OST_IOSAttachedDetailGroups),
        int(BuiltInCategory.OST_IOSModelGroups),
        # int(BuiltInCategory.OST_ElectricalEquipmentTags),
        int(BuiltInCategory.OST_ElectricalCircuit),
        int(BuiltInCategory.OST_SwitchSystem),
    ]

    base_view = get_element(3830882)
    target_view = get_element(5693131)
    set_type = ""
    for unit_type in matrix:
        if unit_type in target_view.Name:
            set_type = unit_type
    if not set_type:
        raise Exception(f"No type for view [{target_view.Name}] set in matrix") 


    elements_collected = FilteredElementCollector(doc, base_view.Id).WhereElementIsNotElementType().ToElements()
    elements_filtered = []
    element_tags = []
    
    for e in elements_collected:
        category = e.Category
        if not category or (category and category.Id.IntegerValue not in include_categories): continue
        if category.Id.IntegerValue == int(BuiltInCategory.OST_IOSAttachedDetailGroups):
            element_tags.append(e)
            continue
        elements_filtered.append(e)


    copied_ids = ElementTransformUtils.CopyElements(
                base_view, 
                List[ElementId](e.Id for e in elements_filtered), 
                target_view, 
                Transform.Identity,
                CopyPasteOptions())

    for id in copied_ids:
        elem = get_element(id)

        # Groups
        if is_category_this(elem, BuiltInCategory.OST_IOSModelGroups):
            # Set detail groups
            attached_detail = elem.GetAvailableAttachedDetailGroupTypeIds()
            attached_detail_list = list(attached_detail)
            if len(attached_detail) == 1:
                elem.ShowAttachedDetailGroups(target_view, attached_detail_list[0])
            else:
                attached = False
                for detail in attached_detail_list:
                    detail_elem = get_element(detail)
                    detail_name = get_parameter(detail_elem, "Type Name")
                    print(detail_name)
                    if matrix[set_type] in detail_name:
                        elem.ShowAttachedDetailGroups(target_view, detail_elem.Id)
                        attached = True
                if not attached:
                    raise Exception(f"No detail attached to {elem.Name}")
                
            # Set workset
            for wrkst in workset:
                if wrkst in elem.Name:
                    set_parameter(elem, "Workset", workset[wrkst])
                    break

        
        # Panel Board
        if is_category_this(elem, BuiltInCategory.OST_ElectricalEquipment):

            # Set panel name
            panel_name = get_parameter(elem, "Panel Name")
            y = panel_name.split(" ", 1)

            unit_no = y[0]
            panel_type = y[1]

            panel_name_new = unit_no[0] + target_view.Name.split(" ")[1] + " " + panel_type
            set_parameter(elem, "Panel Name", panel_name_new) 

            # Set Schedule Level
            set_parameter(elem, "Schedule Level", target_view.GenLevel.Id)

            # Set workset
            if get_parameter(elem, "Family") == "Unit Panel Board": 
                set_parameter(elem, "Workset", workset["Panel"]) 
                
                template_id = ""
                if "A1" in panel_name:
                    template_id = ElementId(7178103)
                elif "A2":
                    template_id = ElementId(7123164)
                ps_view = PanelScheduleView.CreateInstanceView(doc, template_id, elem.Id)


                a2_spares = [
                    [14, 1],
                    [10, 6],
                    [11, 6],
                    [12, 6],
                    [13, 6],
                    [14, 6],
                    [15, 6], 
                ] 

                a2_double_pole = [14, 1]
 

                for sp in a2_spares:
                    r = sp[0]
                    c = sp[1]
                    ps_view.AddSpare(r, c)

                    es = ps_view.GetCircuitByCell(r, c)
                    set_parameter(es, "Load Name", "SPARE")
                    if sp == [14, 1]:
                        set_parameter(es, "Number of Poles", 2)

            if get_parameter(elem, "Family") == "Data Panel Board": 
                set_parameter(elem, "Workset", workset["HMC"]) 

if activate: 
    start()  
  
OUT = output.getvalue() 