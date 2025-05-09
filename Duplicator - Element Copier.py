# Import
import clr
import sys
import time
import re
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
        # print("Starting Transaction")
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        # print("Ending Transaction")
        TransactionManager.Instance.TransactionTaskDone()

# importing lib
activate = IN[1] # type: ignore
for script in IN[0]: # type: ignore
    exec(script)

# Functions and matrix definition
matrix_a: dict[str, any] = locals().get("matrix_a")
matrix_b: dict[str, any] = locals().get("matrix_b")
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
    "A": matrix_a,
    "B": matrix_b
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
    "B1": ElementId(7665512),
    "B2": ElementId(7665511),
    "B3": ElementId(7668613)
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
    },
    "B1": {
        "spares": [
            [13 , 1],
            [14 , 1],
            [6  , 6], 
            [7  , 6],
            [13 , 6],
            [14 , 6],
        ],
        "double": []
    },
    "B2": {
        "spares": [
            [13 , 1],
            [14 , 1],
            [15 , 1],
            [16 , 1],
            [17 , 1],
            [18 , 1],
            [16 , 6],
            [17 , 6],
        ],
        "double": []
    },
    "B3": {
        "spares": [
            [13 , 1],
            [14 , 1],
            [15 , 1],
            [16 , 1],
            [17 , 1],
            [18 , 6],
            [19 , 6],
            [20 , 6],
        ],
        "double": []
    },
}

 
def viewname_get_unit_type(view_name):
    return view_name.split(" ")[-1].rsplit("-", 1)[0]
        
 
 
def get_unit_type(view_name,TOWER):
    view_unit_name = view_name.split(" ", 1)[-1].rsplit('-', 1)[0][2:].strip()
    set_type = "x"
    for unit_name in matrix[TOWER]:
        # print(unit_name)
        unit = matrix[TOWER][unit_name]
        if unit_name in view_unit_name:
            set_type = unit.ortn
        elif unit.pos:
            for lvl in unit.pos:
                unit_name_2 = unit.pos[lvl] + " " + unit_name.split(" ")[1]
                if unit_name_2 in view_unit_name:
                    set_type = unit.ortn
                    return set_type
    if set_type == "x":
        print("NO UNIT FOR: ", view_unit_name)
        # raise Exception(f"No type for view [{view_name}] set in matrix") 
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

def get_dependent_views(target_group:str, target_subgroup: str):
    views: List[ViewPlan] = get_view_range(target_group, target_subgroup, "Unit Rough-Ins")
    units = {}
    for view in views:
        dependent_ids = view.GetDependentViewIds()
        if not dependent_ids: continue
        num = get_num(view.Name)
        units[num] = dependent_ids
    return units
 
def start():
    TARGET_LEVEL = 4
    TOWER = "A"
    TARGET_UNIT = "W_Device Unit 04 (10 A-2AR)"
    # Source views
    source_units = get_dependent_views("1. Working Views", "b. Tower A")

    # Target views
    target_units = get_dependent_views("2. Presentation Views", "b. Tower A")

 
    # Iterate through base view of each level source views based on working views
    for sview_id in source_units[TARGET_LEVEL]:
  
        base_view = get_element(sview_id)
        if base_view.Name != TARGET_UNIT: continue

        unit_name = re.search(r"\((.*?)\)", base_view.Name).group(1)
        unit = matrix_a[unit_name]
        level = get_num(base_view.GenLevel.Name)
 
        # Iterate through target units from presentation views based on level
        for tview_lvl in target_units:
            if tview_lvl in unit.exclude: continue
            # Skip if same level as target view
            if tview_lvl == level: continue
            # Skip if not level range
            if not (unit.min <= tview_lvl <= unit.max): continue

            # Rename position dependent
            unit_name_2 = unit_name
            if tview_lvl in unit.pos:
                unit_name_2 = unit.pos[tview_lvl] + " " + unit_name.split(" ")[1]

            # Iterate through dependent views of each target_unit level view
            for tview_id in target_units[tview_lvl]:
                target_view = get_element(tview_id)
                if unit_name_2 not in target_view.Name: continue

                # print(f"{base_view.Name} - {unit_name_2} - {target_view.Name}")
                place_unit(base_view, target_view, TOWER)
                target_view.Dispose()
                # return 
        
        base_view.Dispose()

def custom_place_tower_b():
    source = get_dependent_views("2. Presentation Views", "c. Tower B")

    level_8 = source[8] 
    level_9 = source[9]

    source_views = {}
    unit_views = {}

    for sid in level_8:
        base_view = get_element(sid)
        unit_name = base_view.Name.replace("UNIT ", "")[2:].rsplit("-", 1)[0]
        source_views[unit_name] = base_view


    for tid in level_9:
        base_view = get_element(tid)
        unit_name = base_view.Name.replace("UNIT ", "")[2:].rsplit("-", 1)[0]
        unit_views[unit_name] = base_view
    done = [] 
    target_shit = "09 BPR-1D"
    for base_name in source_views:

        if base_name != target_shit: continue
        # if base_name in done: continue
        for target_name in unit_views:
            if base_name == target_name:
                base_view = source_views[base_name]
                target_view = unit_views[target_name]
                place_unit(base_view, target_view, "B")
                done.append(base_name)


def place_unit(base_view: ViewPlan, target_view: ViewPlan, TOWER: str):
 
    include_categories = [
        int(BuiltInCategory.OST_ElectricalEquipment),
        int(BuiltInCategory.OST_IOSModelGroups),
        int(BuiltInCategory.OST_ElectricalCircuit), 
        int(BuiltInCategory.OST_SwitchSystem),
        # int(BuiltInCategory.OST_ElectricalEquipmentTags), 
    ] 
    # base_view = get_element(3830970)
    # target_view = get_element(5693191)

    set_type = get_unit_type(target_view.Name, TOWER)
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

                    if set_type in detail_name:
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
    custom_place_tower_b()  
  
OUT = output.getvalue() 