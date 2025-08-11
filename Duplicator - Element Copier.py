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
collect_elements = globals().get("collect_elements")
UnitView = locals().get("UnitView")
get_unit_key = locals().get("get_unit_key")
#==== Template ends here ====# 


# Parameters
matrix = {
    "A": matrix_a,
    "B": matrix_b
}

subgroup = {
    "A": "b. Tower A",
    "B": "c. Tower B"
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
    "A2.1": ElementId(9573549),
    "A3": ElementId(8642555),
    "A3.1": ElementId(9372255),
    "A3.2": ElementId(9222896),
    "A3.3": ElementId(8749398),
    "A3.4": ElementId(9539422),
    "A3.5": ElementId(8749398),
    "A3.6": ElementId(13240420),
    "B1": ElementId(7665512),
    "B2": ElementId(7665511),
    "B3": ElementId(7668613)
}
panel_spares = {
    "A1": {
        "spares": [
            [14, 1],
            [13, 6],
            [14, 6],
            [15, 6],
            [16, 6],
        ],
        "double": [[14, 1]]
    },
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
    "A2.1": {
        "spares": [[14, 1]],
        "double": [[14, 1]],
    },
    "A3": {
        "spares": [
            [14, 1],
            [7, 6],
            [10 , 6],
            [11 , 6],
            [12 , 6],
            [13 , 6],
            [18 , 6],
            [19 , 6],
        ],
        "double": [[14, 1]]
    },
    "A3.1": {
        "spares": [
            [14, 1],
            [7, 6],
            [20, 6],
            [21, 6],
            [22, 6],
        ],
        "double": [[14, 1]] ,
    },
    "A3.2": {
        "spares": [
            [14, 1],
            [16, 6]
        ],
        "double": [[14, 1]],
    },
    "A3.3": {
        "spares": [
            [14, 1],
            [12, 6],
            [13, 6],
            [14, 6],
            [15, 6],
            [16, 6],
        ],
        "double": [[14, 1]],
    },
    "A3.4": {
        "spares": [
            [14, 1],
            [17, 6],
            [7, 6],
        ],
        "double": [[14, 1]],
    },
    "A3.5": {
        "spares": [
            [10, 6],
            [11, 6],
            [12, 6],
            [13, 6],
            [14, 6],
            [15, 6],
        ],
        "double": [],
    },
    "A3.6": {
        "spares": [
            [14, 1],
            [7, 6],
            [13, 6],
            [15, 6],
        ],
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

 
@transaction
def copy_elements(base_view, target_view, elements_filtered):
    copied_ids = ElementTransformUtils.CopyElements(
                base_view, 
                List[ElementId](e.Id for e in elements_filtered), 
                target_view, 
                Transform.Identity,
                CopyPasteOptions())
    return copied_ids

def _get_dependent_views(target_group:str, target_subgroup: str):
    views: List[ViewPlan] = get_view_range(target_group, target_subgroup, "Unit Rough-Ins")
    units = {}
    for view in views:
        dependent_ids = view.GetDependentViewIds()
        if not dependent_ids: continue
        num = get_num(view.Name)
        units[num] = dependent_ids
    return units

def get_working_matrix_name(view: ViewPlan) -> str:
    return re.search(r"\((.*?)\)", view.Name).group(1)

def get_tower(view_name) -> str:
    return view_name.split("-")[0].strip()[-1]

def start():
    print("asdasd")
    # Parameters   
    TARGET_UNIT = "W_Unit 02 (02 A-2AR)"
    TOWER = get_tower(TARGET_UNIT)

    # Source views   
    source_units = get_view_range("1. Working Views", subgroup[TOWER], "Unit Rough-Ins", dependent_only=True)

    # Target views
    target_units = _get_dependent_views("2. Presentation Views", subgroup[TOWER])
 
    source_view = ""
    # Get source view
    for sview in source_units:
        if sview.Name != TARGET_UNIT: continue
        source_view = sview

    # Get name and matrix
    unit_name = get_working_matrix_name(source_view)
    m_unit = matrix[TOWER][unit_name]
        
    # Iterate through target units from presentation views based on level
    for level in target_units:
        # Checks
        if level in m_unit.exclude: continue
        if level == get_num(source_view.GenLevel.Name): continue # Skip if same level as target view
        if not (m_unit.min <= level <= m_unit.max): continue # Skip if not level range

        # Rename position dependent
        positional_name = unit_name # e.g. 02 A-3A
        if level in m_unit.pos:
            positional_name = f'{m_unit.pos[level]}  {unit_name.split(" ")[1]}'

        # Iterate through dependent views of each target_unit level view
        for tview_id in target_units[level]:
            target_view = get_element(tview_id)
            if positional_name not in target_view.Name: continue
            print(target_view.Name, positional_name)
            place_unit(source_view, target_view, TOWER)
            target_view.Dispose()

    source_view.Dispose()

def custom_place_tower_b():
    source = _get_dependent_views("2. Presentation Views", "c. Tower B")

    source_level = source[3] 
    target_level = source[4]

    source_views = {}
    unit_views = {}

    for sid in source_level:
        base_view = get_element(sid)
        unit_name = base_view.Name.replace("UNIT ", "")[2:].rsplit("-", 1)[0]
        source_views[unit_name] = base_view


    for tid in target_level:
        base_view = get_element(tid)
        unit_name = base_view.Name.replace("UNIT ", "")[2:].rsplit("-", 1)[0]
        unit_views[unit_name] = base_view
    done = [] 
    target_shit = "01 BPR-1C"
    # target_shit = "13 BPR-2A"
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
    ] 

    # set_type = get_unit_type(target_view.Name, TOWER)
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
            # if "RCP" in elem.Name or "Fire" in elem.Name:
            #     set_parameter(elem, "Origin Level Offset", "-0'  9\"") 
            # # Set detail groups
            # attached_detail = elem.GetAvailableAttachedDetailGroupTypeIds()
            # attached_detail_list = list(attached_detail)
            # if len(attached_detail) == 1:
            #     with Transact():
            #         elem.ShowAttachedDetailGroups(target_view, attached_detail_list[0])
            # else:
            #     attached = False
            #     for detail in attached_detail_list:
            #         detail_elem = get_element(detail)
            #         detail_name = get_parameter(detail_elem, "Type Name")

            #         if set_type in detail_name:
            #             with Transact():
            #                 elem.ShowAttachedDetailGroups(target_view, detail_elem.Id)
            #             attached = True

            #         # Disposal
            #         detail_elem.Dispose() 
            #         del detail_name
            #     if not attached:
            #         raise Exception(f"No detail attached to {elem.Name}")
                
            # Set workset
            for wrkst in workset:
                if wrkst in elem.Name:
                    with Transact():
                        set_parameter(elem, "Workset", workset[wrkst])
                    break
            
            # # Disposal
            # del attached_detail
            # del attached_detail_list
        
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