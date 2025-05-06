# Import
import clr
import sys
import time
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

class Transact:
    def __init__(self):
        TransactionManager.Instance.EnsureInTransaction(doc)
    def __enter__(self):
        print("Starting Transaction")
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        print("Ending Transaction")
        TransactionManager.Instance.TransactionTaskDone()

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

# Parameters
matrix = {
    "01 A-2A": "Right",
    "05 A-1BR": "",
    "06 A-1B": ""
}

workset = {
    "RCP": 783,
    "Power": 784,
    "Fire": 785,
    "Panel": 835,
    "HMC": 778,
}

panel_template = {
    "A1": ElementId(7178103),
    "A2": ElementId(7123164),
}
panel_spares = {
    "A2": {
        "spares": [
            [14, 1],
            [10, 6],
            [11, 6],
            [12, 6],
            [13, 6],
            [14, 6],
            [15, 6], 
        ],
        "double": [[14, 1]]
    },
    "A1": {
        "spares": [[14, 1]],
        "double": [[14, 1]],
    }
}


def get_unit_type(view_name):
    set_type = ""
    for unit_type in matrix:
        if unit_type in view_name:
            set_type = unit_type
    if not set_type:
        raise Exception(f"No type for view [{view_name}] set in matrix") 
    return set_type

@transaction
def copy_elements(base_view, target_view, elements_filtered):
    copied_ids = ElementTransformUtils.CopyElements(
                base_view, 
                List[ElementId](e.Id for e in elements_filtered), 
                target_view, 
                Transform.Identity,
                CopyPasteOptions())
    return copied_ids

# Body
def start():

    include_categories = [
        int(BuiltInCategory.OST_ElectricalEquipment),
        int(BuiltInCategory.OST_IOSModelGroups),
        int(BuiltInCategory.OST_ElectricalCircuit), 
        int(BuiltInCategory.OST_SwitchSystem),
        # int(BuiltInCategory.OST_ElectricalEquipmentTags), 
    ] 
    base_view = get_element(3830970)
    target_view = get_element(5693191)

    set_type = get_unit_type(target_view.Name)

    element_collector = FilteredElementCollector(doc, base_view.Id)
    elements_filtered = []
    element_tags = []
    
    # elements filter
    for e in element_collector.WhereElementIsNotElementType().ToElements():
  
        category = e.Category
        if not category or (category and category.Id.IntegerValue not in include_categories): continue
        if category.Id.IntegerValue == int(BuiltInCategory.OST_IOSAttachedDetailGroups):
            element_tags.append(e)
            continue
        elements_filtered.append(e)

    # Copy elements
    copied_ids = []
    with Transact():
        copied_ids = ElementTransformUtils.CopyElements(
                    base_view, 
                    List[ElementId](e.Id for e in elements_filtered), 
                    target_view, 
                    Transform.Identity,
                    CopyPasteOptions())


    # disposal
    element_collector.Dispose()
    del elements_filtered
    del include_categories
    # disposal

    for id in copied_ids:
        elem = get_element(id)

        # Groups
        if is_category_this(elem, BuiltInCategory.OST_IOSModelGroups):
            # Set detail groups
            attached_detail = elem.GetAvailableAttachedDetailGroupTypeIds()
            attached_detail_list = list(attached_detail)
            if len(attached_detail) == 1:
                with Transact():
                    elem.ShowAttachedDetailGroups(target_view, attached_detail_list[0])
            else:
                attached = False
                for detail in attached_detail_list:
                    detail_elem = get_element(detail)
                    detail_name = get_parameter(detail_elem, "Type Name")

                    if matrix[set_type] in detail_name:
                        with Transact():
                            elem.ShowAttachedDetailGroups(target_view, detail_elem.Id)
                        attached = True

                    # Disposal
                    detail_elem.Dispose()
                    del detail_name
                if not attached:
                    raise Exception(f"No detail attached to {elem.Name}")
                
            # Set workset
            for wrkst in workset:
                if wrkst in elem.Name:
                    with Transact():
                        set_parameter(elem, "Workset", workset[wrkst])
                    break
            
            # Disposal
            del attached_detail
            del attached_detail_list
        
        # Panel Board
        if is_category_this(elem, BuiltInCategory.OST_ElectricalEquipment):
            family_type = get_parameter(elem, "Family")
            if family_type not in ["Unit Panel Board", "Data Panel Board"]: continue 

            # Set panel name
            panel_name = get_parameter(elem, "Panel Name")
            y = panel_name.split(" ", 1)

            unit_no = y[0]
            panel_type = y[1].split(" ")[-1]

 
            panel_name_new = unit_no[0] + target_view.Name.split(" ")[1] + " PNL " + panel_type

            with Transact():
                set_parameter(elem, "Panel Name", panel_name_new)  
                set_parameter(elem, "Unit no.", target_view.Name.split(" ")[1])
                # Set Schedule Level
                set_parameter(elem, "Schedule Level", target_view.GenLevel.Id)

            # Set workset
            if family_type == "Unit Panel Board": 
                with Transact():
                    set_parameter(elem, "Workset", workset["Panel"]) 
                    
                    template_id = panel_template[panel_type]
                    ps_view = PanelScheduleView.CreateInstanceView(doc, template_id, elem.Id)
                    
                    for sp in panel_spares[panel_type]["spares"]:
                        r = sp[0] 
                        c = sp[1]
                        ps_view.AddSpare(r, c)

                        es = ps_view.GetCircuitByCell(r, c)
                        set_parameter(es, "Load Name", "SPARE")
                        if sp in panel_spares[panel_type]["double"]:
                            set_parameter(es, "Number of Poles", 2)
                
                # Disposal
                ps_view.Dispose()

            if family_type == "Data Panel Board": 
                with Transact():
                    set_parameter(elem, "Workset", workset["HMC"]) 

        if elem:
            elem.Dispose()
            del elem
if activate: 
    start()  
  
OUT = output.getvalue() 