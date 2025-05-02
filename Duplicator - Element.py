# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, CopyPasteOptions, ViewPlan, Transform, ElementTransformUtils, FilteredElementCollector

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

class Stairs:
    def __init__(self, target_view,num):
        self.num = num
        self.target_view = target_view

# Parameters

# Body 
@transaction     
def start():

    target_stair = "B-S2"
    stair_views_list = []
    stair_views = get_view_range("2. Presentation Views", "d. Enlarged", "Stairs")
    for stair in stair_views:
        if target_stair not in stair.Name: continue
        stair_views_list.append(stair)



    target_view = 6268894

    for stair_view in stair_views_list:
        num = get_num(stair_view.GenLevel.Name)
        if num in [1, 2]: continue
        print(num, stair_view.Name)

        element_list = [4471092, 6290717]

        copied_ids = ElementTransformUtils.CopyElements(
            get_element(target_view), 
            List[ElementId](ElementId(e) for e in element_list), 
            stair_view, 
            Transform.Identity,
            CopyPasteOptions()
        )
        for id in copied_ids:
            celem = get_element(id)
            parameter = celem.LookupParameter("Schedule Level")
            parameter.Set(stair_view.GenLevel.Id)

if activate:   
    start()  
 
OUT = output.getvalue()  



